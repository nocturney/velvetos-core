package platform

import (
	"errors"
	"net/http"
	"testing"
)

func TestVelvetExternalIDUsesMediaID(t *testing.T) {
	got := velvetExternalID(map[string]any{"media_id": "17948586183272855"})
	if got != "17948586183272855" {
		t.Fatalf("got %q", got)
	}
}

func TestVelvetExternalIDIgnoresMissingAndNonStringValues(t *testing.T) {
	got := velvetExternalID(map[string]any{
		"id":  nil,
		"media_id": " 17948586183272855 ",
	})
	if got != "17948586183272855" {
		t.Fatalf("got %q", got)
	}
}

func TestVelvetRemoteFailureMessageUsesSafeFields(t *testing.T) {
	got := velvetRemoteFailureMessage(map[string]any{
		"ok":          false,
		"error_class": "oauth",
		"error":       "Media ID is not available",
	})
	want := "class=oauth; Media ID is not available"
	if got != want {
		t.Fatalf("got %q want %q", got, want)
	}
}

func TestVelvetRemoteFailureMessageFallback(t *testing.T) {
	if got := velvetRemoteFailureMessage(map[string]any{"ok": false}); got != "mutation rejected" {
		t.Fatalf("got %q", got)
	}
}

func TestVelvetRateLimitIsDefiniteAndTyped(t *testing.T) {
	err := velvetRemoteFailureError(map[string]any{"ok": false, "error_class": "rate_limited", "error": "rate limited"})
	if !velvetDefinitelyRejected(err) { t.Fatal("expected definite rejection") }
	var httpErr *HTTPError
	if !errors.As(err, &httpErr) { t.Fatal("expected HTTPError") }
	if httpErr.StatusCode != http.StatusTooManyRequests { t.Fatalf("status=%d", httpErr.StatusCode) }
	if httpErr.Code != "velvet:rate_limited" { t.Fatalf("code=%q", httpErr.Code) }
}

func TestVelvetTimeoutIsAmbiguousAndTyped(t *testing.T) {
	err := velvetRemoteFailureError(map[string]any{"ok": false, "error_class": "timeout", "error": "Graph API timed out"})
	if velvetDefinitelyRejected(err) { t.Fatal("timeout must not be marked definitely rejected") }
	var httpErr *HTTPError
	if !errors.As(err, &httpErr) { t.Fatal("expected HTTPError") }
	if httpErr.StatusCode != http.StatusRequestTimeout { t.Fatalf("status=%d", httpErr.StatusCode) }
	if ProviderSafeMessage(err) == "" { t.Fatal("expected safe provider message") }
}