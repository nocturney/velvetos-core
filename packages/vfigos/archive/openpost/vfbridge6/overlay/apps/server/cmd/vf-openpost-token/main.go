package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/openpost/backend/internal/database"
	"github.com/openpost/backend/internal/models"
	"github.com/openpost/backend/internal/services/apitokens"
	"github.com/uptrace/bun"
)

type tokenMeta struct {
	TokenID string `json:"token_id"`
	UserID string `json:"user_id"`
	WorkspaceID string `json:"workspace_id"`
}

func main() {
	mode := flag.String("mode", "issue", "issue or revoke")
	dbPath := flag.String("db", "", "OpenPost SQLite DSN/path")
	tokenFile := flag.String("token-file", "/run/openpost-vf/api.token", "raw token file")
	metaFile := flag.String("meta-file", "/run/openpost-vf/api-token-meta.json", "token metadata file")
	flag.Parse()
	if *dbPath == "" {
		*dbPath = os.Getenv("OPENPOST_DATABASE_PATH")
	}
	if *dbPath == "" {
		fmt.Fprintln(os.Stderr, "database path is required")
		os.Exit(2)
	}
	db, err := database.InitDB(*dbPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, "open database:", err)
		os.Exit(1)
	}
	defer db.Close()

	switch *mode {
	case "issue":
		if err := issue(db, *tokenFile, *metaFile); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	case "revoke":
		if err := revoke(db, *tokenFile, *metaFile); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	default:
		fmt.Fprintln(os.Stderr, "mode must be issue or revoke")
		os.Exit(2)
	}
}
func issue(db *bun.DB, tokenFile, metaFile string) error {
	ctx := context.Background()
	var users []models.User
	if err := db.NewSelect().Model(&users).Scan(ctx); err != nil {
		return fmt.Errorf("list users: %w", err)
	}
	var workspaces []models.Workspace
	if err := db.NewSelect().Model(&workspaces).Scan(ctx); err != nil {
		return fmt.Errorf("list workspaces: %w", err)
	}
	if len(users) != 1 || len(workspaces) != 1 {
		return fmt.Errorf("refusing token issue: expected exactly one user and one workspace, got users=%d workspaces=%d", len(users), len(workspaces))
	}
	expiry := time.Now().UTC().Add(time.Hour)
	generated, err := apitokens.NewService(db).GenerateTokenWithOptions(
		ctx, users[0].ID, "velvet-promotion-one-shot", apitokens.ScopeAPIWrite,
		apitokens.GenerateOptions{ExpiresAt: &expiry, WorkspaceID: workspaces[0].ID},
	)
	if err != nil {
		return fmt.Errorf("generate api token: %w", err)
	}
	if err := os.MkdirAll(filepath.Dir(tokenFile), 0o700); err != nil {
		return err
	}
	if err := os.WriteFile(tokenFile, []byte(generated.Token+"\n"), 0o600); err != nil {
		return err
	}
	meta := tokenMeta{TokenID: generated.Model.ID, UserID: users[0].ID, WorkspaceID: workspaces[0].ID}
	raw, _ := json.Marshal(meta)
	if err := os.WriteFile(metaFile, raw, 0o600); err != nil {
		return err
	}
	fmt.Printf("issued token_id=%s workspace_id=%s expires_at=%s\n", meta.TokenID, meta.WorkspaceID, expiry.Format(time.RFC3339))
	return nil
}

func revoke(db *bun.DB, tokenFile, metaFile string) error {
	ctx := context.Background()
	raw, err := os.ReadFile(metaFile)
	if err != nil {
		return fmt.Errorf("read token metadata: %w", err)
	}
	var meta tokenMeta
	if err := json.Unmarshal(raw, &meta); err != nil {
		return fmt.Errorf("decode token metadata: %w", err)
	}
	if err := apitokens.NewService(db).RevokeToken(ctx, meta.UserID, meta.TokenID); err != nil {
		return fmt.Errorf("revoke api token: %w", err)
	}
	_ = os.Remove(tokenFile)
	_ = os.Remove(metaFile)
	fmt.Printf("revoked token_id=%s\n", meta.TokenID)
	return nil
}
