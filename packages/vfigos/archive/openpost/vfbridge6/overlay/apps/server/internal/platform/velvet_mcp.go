package platform

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

type velvetApprovalEnvelope struct {
	DeliveryApproval json.RawMessage `json:"delivery_approval"`
	ContentID string `json:"content_id"`
	PackageSHA256 string `json:"package_sha256"`
	MediaURLs []string `json:"media_urls"`
	MutationTool string `json:"mutation_tool"`
	MutationArgs map[string]any `json:"mutation_args"`
}

type velvetMCPClient struct {
	url string
	bearer string
	http *http.Client
}

type velvetDefiniteError struct{ err error }

func (e *velvetDefiniteError) Error() string { return e.err.Error() }
func (e *velvetDefiniteError) Unwrap() error { return e.err }

type velvetRemoteError struct {
	class   string
	message string
	cause   error
}

func (e *velvetRemoteError) Error() string {
	if strings.TrimSpace(e.message) != "" {
		return fmt.Sprintf("Velvet MCP %s: %s", e.class, strings.TrimSpace(e.message))
	}
	return fmt.Sprintf("Velvet MCP %s", e.class)
}
func (e *velvetRemoteError) Unwrap() error { return e.cause }
func (e *velvetRemoteError) SafeProviderMessage() string { return strings.TrimSpace(e.message) }

func velvetDefinitelyRejected(err error) bool {
	var target *velvetDefiniteError
	return errors.As(err, &target)
}
func velvetMCPConfigured() bool {
	return strings.TrimSpace(os.Getenv("VELVET_INSTAGRAM_MCP_URL")) != ""
}

func loadVelvetApproval(renditionID string) (*velvetApprovalEnvelope, func(), error) {
	dir := strings.TrimSpace(os.Getenv("VELVET_OPENPOST_APPROVAL_DIR"))
	if dir == "" {
		return nil, nil, fmt.Errorf("VELVET_OPENPOST_APPROVAL_DIR is required")
	}
	id := strings.TrimSpace(renditionID)
	if id == "" || filepath.Base(id) != id {
		return nil, nil, fmt.Errorf("invalid rendition id for approval lookup")
	}
	src := filepath.Join(dir, id+".json")
	claimed := src + ".consuming"
	if err := os.Rename(src, claimed); err != nil {
		return nil, nil, fmt.Errorf("claiming Velvet approval envelope: %w", err)
	}
	cleanup := func() { _ = os.Remove(claimed) }
	raw, err := os.ReadFile(claimed)
	if err != nil {
		cleanup()
		return nil, nil, err
	}
	// PowerShell 5.1 writes UTF-8 BOM by default. Accept it at this boundary
	// so an otherwise valid owner-signed approval cannot fail before MCP.
	raw = bytes.TrimPrefix(raw, []byte{0xEF, 0xBB, 0xBF})
	var env velvetApprovalEnvelope
	if err := json.Unmarshal(raw, &env); err != nil {
		cleanup()
		return nil, nil, fmt.Errorf("decoding Velvet approval envelope: %w", err)
	}
	if len(env.DeliveryApproval) == 0 || env.ContentID == "" || env.PackageSHA256 == "" || len(env.MediaURLs) == 0 || env.MutationTool == "" || len(env.MutationArgs) == 0 {
		cleanup()
		return nil, nil, fmt.Errorf("incomplete Velvet approval envelope")
	}
	return &env, cleanup, nil
}

func newVelvetMCPClient() (*velvetMCPClient, error) {
	url := strings.TrimSpace(os.Getenv("VELVET_INSTAGRAM_MCP_URL"))
	bearerFile := strings.TrimSpace(os.Getenv("VELVET_INSTAGRAM_MCP_BEARER_FILE"))
	if url == "" || bearerFile == "" {
		return nil, fmt.Errorf("Velvet MCP URL/bearer file not configured")
	}
	raw, err := os.ReadFile(bearerFile)
	if err != nil {
		return nil, fmt.Errorf("reading Velvet MCP bearer file: %w", err)
	}
	bearer := strings.TrimSpace(string(raw))
	if bearer == "" {
		return nil, fmt.Errorf("Velvet MCP bearer file is empty")
	}
	return &velvetMCPClient{url: strings.TrimRight(url, "/"), bearer: bearer, http: &http.Client{Timeout: 90 * time.Second}}, nil
}
func (c *velvetMCPClient) post(ctx context.Context, body any, sid string) ([]byte, string, error) {
	raw, err := json.Marshal(body)
	if err != nil { return nil, sid, err }
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.url, bytes.NewReader(raw))
	if err != nil { return nil, sid, err }
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json, text/event-stream")
	req.Header.Set("Authorization", "Bearer "+c.bearer)
	if sid != "" { req.Header.Set("Mcp-Session-Id", sid) }
	resp, err := c.http.Do(req)
	if err != nil { return nil, sid, err }
	defer resp.Body.Close()
	data, err := io.ReadAll(io.LimitReader(resp.Body, 2<<20))
	if err != nil { return nil, sid, err }
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, sid, fmt.Errorf("Velvet MCP HTTP %d: %s", resp.StatusCode, strings.TrimSpace(string(data)))
	}
	if got := resp.Header.Get("Mcp-Session-Id"); got != "" { sid = got }
	return data, sid, nil
}
func velvetSSEPayload(raw []byte) ([]byte, error) {
	s := strings.TrimSpace(string(raw))
	if strings.HasPrefix(s, "{") { return []byte(s), nil }
	for _, line := range strings.Split(s, "\n") {
		if strings.HasPrefix(line, "data: ") {
			return []byte(strings.TrimSpace(strings.TrimPrefix(line, "data: "))), nil
		}
	}
	return nil, fmt.Errorf("Velvet MCP returned no JSON/SSE payload")
}

func (c *velvetMCPClient) call(ctx context.Context, tool string, args map[string]any) (map[string]any, error) {
	initBody := map[string]any{"jsonrpc":"2.0","id":1,"method":"initialize","params":map[string]any{
		"protocolVersion":"2025-03-26","capabilities":map[string]any{},"clientInfo":map[string]any{"name":"openpost-velvet-bridge","version":"1"},
	}}
	raw, sid, err := c.post(ctx, initBody, "")
	if err != nil { return nil, err }
	if _, err := velvetSSEPayload(raw); err != nil { return nil, err }
	_, sid, err = c.post(ctx, map[string]any{"jsonrpc":"2.0","method":"notifications/initialized"}, sid)
	if err != nil { return nil, err }
	callBody := map[string]any{"jsonrpc":"2.0","id":2,"method":"tools/call","params":map[string]any{"name":tool,"arguments":args}}
	raw, _, err = c.post(ctx, callBody, sid)
	if err != nil { return nil, err }
	payloadRaw, err := velvetSSEPayload(raw)
	if err != nil { return nil, err }
	var payload struct {
		Error any `json:"error"`
		Result struct {
			Content []struct { Type string `json:"type"`; Text string `json:"text"` } `json:"content"`
			IsError bool `json:"isError"`
		} `json:"result"`
	}
	if err := json.Unmarshal(payloadRaw, &payload); err != nil { return nil, err }
	if payload.Error != nil {
		return nil, fmt.Errorf("Velvet MCP RPC error")
	}
	for _, item := range payload.Result.Content {
		if item.Type != "text" || item.Text == "" { continue }
		var out map[string]any
		if err := json.Unmarshal([]byte(item.Text), &out); err != nil { continue }
		if ok, exists := out["ok"].(bool); exists && !ok {
			return nil, velvetRemoteFailureError(out)
		}
		if payload.Result.IsError {
			return nil, fmt.Errorf("Velvet MCP tool error: %s", item.Text)
		}
		return out, nil
	}
	if payload.Result.IsError {
		return nil, fmt.Errorf("Velvet MCP tool call failed")
	}
	return nil, fmt.Errorf("Velvet MCP returned no tool result")
}

func velvetRemoteFailureMessage(out map[string]any) string {
	parts := make([]string, 0, 3)
	if class, ok := out["error_class"].(string); ok && strings.TrimSpace(class) != "" {
		parts = append(parts, "class="+strings.TrimSpace(class))
	}
	if message, ok := out["error"].(string); ok && strings.TrimSpace(message) != "" {
		parts = append(parts, strings.TrimSpace(message))
	}
	if problems, exists := out["problems"]; exists && problems != nil {
		parts = append(parts, fmt.Sprintf("problems=%v", problems))
	}
	if len(parts) == 0 {
		return "mutation rejected"
	}
	return strings.Join(parts, "; ")
}

func velvetRemoteFailureError(out map[string]any) error {
	class, _ := out["error_class"].(string)
	class = strings.TrimSpace(class)
	if class == "" {
		class = "upstream_error"
	}
	message := velvetRemoteFailureMessage(out)
	status := http.StatusBadGateway
	definite := false
	switch class {
	case "delivery_approval", "validation", "invalid_param", "ssrf_blocked", "not_found":
		status = http.StatusUnprocessableEntity
		definite = true
	case "oauth", "auth":
		status = http.StatusUnauthorized
		definite = true
	case "permission", "needs_app_review":
		status = http.StatusForbidden
		definite = true
	case "rate_limited":
		status = http.StatusTooManyRequests
		definite = true
	case "timeout":
		status = http.StatusRequestTimeout
	case "network":
		status = http.StatusServiceUnavailable
	case "upstream_error", "internal_error", "filesystem":
		status = http.StatusBadGateway
	}
	remote := &velvetRemoteError{
		class: class,
		message: message,
		cause: &HTTPError{StatusCode: status, Code: "velvet:" + class},
	}
	if definite {
		return &velvetDefiniteError{err: remote}
	}
	return remote
}

func velvetToolForRequest(req *PublishRequest, mediaURLs []string) (string, map[string]any, error) {
	if req.ReplyToID != "" { return "", nil, fmt.Errorf("Velvet bridge forbids comment replies") }
	if len(mediaURLs) == 0 || len(mediaURLs) != len(req.Media) {
		return "", nil, fmt.Errorf("Velvet bridge requires approved media URLs matching attached media")
	}
	account := strings.TrimSpace(os.Getenv("VELVET_INSTAGRAM_MCP_ACCOUNT"))
	if account == "" { account = "env" }
	args := map[string]any{"account":account}
	if instagramIsStory(req) {
		if len(mediaURLs) != 1 { return "", nil, fmt.Errorf("Velvet story bridge supports one media item") }
		if isVideoMime(req.Media[0].MimeType) { args["video_url"] = mediaURLs[0] } else { args["image_url"] = mediaURLs[0] }
		return "publish_story", args, nil
	}
	if len(mediaURLs) > 1 {
		urls := make([]string, len(mediaURLs))
		for idx, u := range mediaURLs {
			if isVideoMime(req.Media[idx].MimeType) { return "", nil, fmt.Errorf("Velvet carousel bridge currently requires image-only carousel") }
			urls[idx] = u
		}
		args["image_urls"] = urls
		args["caption"] = req.Content
		return "publish_carousel", args, nil
	}
	if isVideoMime(req.Media[0].MimeType) {
		args["video_url"] = mediaURLs[0]
		args["caption"] = req.Content
		if instagramIsReel(req) {
			if _, ok := req.Settings["share_to_feed"]; ok {
				args["share_to_feed"] = settingBool(req.Settings, "share_to_feed")
			}
			return "publish_reel", args, nil
		}
		return "publish_video", args, nil
	}
	args["image_url"] = mediaURLs[0]
	args["caption"] = req.Content
	return "publish_image", args, nil
}

func validateVelvetMutationBinding(tool string, actual map[string]any, env *velvetApprovalEnvelope) error {
	if tool != env.MutationTool {
		return fmt.Errorf("Velvet approval tool mismatch: openpost=%s approved=%s", tool, env.MutationTool)
	}
	if len(actual) != len(env.MutationArgs) {
		return fmt.Errorf("Velvet approval argument set mismatch")
	}
	for key, actualValue := range actual {
		approvedValue, ok := env.MutationArgs[key]
		if !ok {
			return fmt.Errorf("Velvet approval missing argument %s", key)
		}
		if key == "caption" {
			actualCaption, aok := actualValue.(string)
			approvedCaption, bok := approvedValue.(string)
			if !aok || !bok || strings.TrimRight(actualCaption, "\r\n") != strings.TrimRight(approvedCaption, "\r\n") {
				return fmt.Errorf("Velvet approval caption mismatch")
			}
			continue
		}
		actualJSON, err := json.Marshal(actualValue)
		if err != nil { return err }
		approvedJSON, err := json.Marshal(approvedValue)
		if err != nil { return err }
		if !bytes.Equal(actualJSON, approvedJSON) {
			return fmt.Errorf("Velvet approval argument mismatch for %s", key)
		}
	}
	return nil
}

func publishInstagramViaVelvetMCP(ctx context.Context, req *PublishRequest) (PublishResult, error) {
	env, cleanup, err := loadVelvetApproval(req.RenditionID)
	if err != nil {
		log.Printf("[VelvetMCP] rendition=%s stage=load_approval error=%v", req.RenditionID, err)
		return PublishResult{}, &velvetDefiniteError{err: err}
	}
	defer cleanup()
	tool, actualArgs, err := velvetToolForRequest(req, env.MediaURLs)
	if err != nil {
		log.Printf("[VelvetMCP] rendition=%s stage=tool_for_request error=%v", req.RenditionID, err)
		return PublishResult{}, &velvetDefiniteError{err: err}
	}
	if err := validateVelvetMutationBinding(tool, actualArgs, env); err != nil {
		log.Printf("[VelvetMCP] rendition=%s stage=validate_binding tool=%s error=%v", req.RenditionID, tool, err)
		return PublishResult{}, &velvetDefiniteError{err: err}
	}
	args := make(map[string]any, len(env.MutationArgs)+3)
	for key, value := range env.MutationArgs { args[key] = value }
	var receipt any
	if err := json.Unmarshal(env.DeliveryApproval, &receipt); err != nil {
		log.Printf("[VelvetMCP] rendition=%s stage=decode_receipt error=%v", req.RenditionID, err)
		return PublishResult{}, &velvetDefiniteError{err: err}
	}
	args["delivery_approval"] = receipt
	args["content_id"] = env.ContentID
	args["package_sha256"] = env.PackageSHA256
	client, err := newVelvetMCPClient()
	if err != nil {
		log.Printf("[VelvetMCP] rendition=%s stage=new_client error=%v", req.RenditionID, err)
		return PublishResult{}, &velvetDefiniteError{err: err}
	}
	log.Printf("[VelvetMCP] rendition=%s stage=preflight_ok tool=%s media_count=%d", req.RenditionID, env.MutationTool, len(env.MediaURLs))
	out, err := client.call(ctx, env.MutationTool, args)
	if err != nil {
		log.Printf("[VelvetMCP] rendition=%s stage=mcp_call error=%v", req.RenditionID, err)
		return PublishResult{}, err
	}
	id := velvetExternalID(out)
	if id == "" {
		err := fmt.Errorf("Velvet MCP mutation returned no media id")
		log.Printf("[VelvetMCP] rendition=%s stage=extract_media_id error=%v", req.RenditionID, err)
		return PublishResult{}, err
	}
	log.Printf("[VelvetMCP] rendition=%s stage=success", req.RenditionID)
	return PublishResult{ExternalID:id}, nil
}

func velvetExternalID(out map[string]any) string {
	for _, key := range []string{"media_id", "id", "external_id"} {
		value, ok := out[key]
		if !ok {
			continue
		}
		s, ok := value.(string)
		if !ok {
			continue
		}
		if trimmed := strings.TrimSpace(s); trimmed != "" {
			return trimmed
		}
	}
	return ""
}
