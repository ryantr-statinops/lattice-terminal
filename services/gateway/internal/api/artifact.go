package api

import (
	"crypto/sha256"
	"encoding/hex"
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

func (a *API) artifactRoutes(m *http.ServeMux) {
	m.HandleFunc("GET /api/v1/runs/{id}/artifacts", func(w http.ResponseWriter, r *http.Request) {
		values, err := a.Store.Artifacts(r.PathValue("id"))
		if err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, values)
	})
	m.HandleFunc("GET /api/v1/runs/{id}/artifacts/{name}", func(w http.ResponseWriter, r *http.Request) {
		values, err := a.Store.Artifacts(r.PathValue("id"))
		if err != nil {
			Fail(w, err)
			return
		}
		for _, v := range values {
			if v.Name != r.PathValue("name") {
				continue
			}
			p := filepath.Join(a.Workspace.Root, filepath.FromSlash(v.Path))
			resolved, err := filepath.EvalSymlinks(p)
			if err != nil {
				http.NotFound(w, r)
				return
			}
			rel, err := filepath.Rel(filepath.Join(a.Workspace.Root, "artifacts"), resolved)
			if err != nil || rel == ".." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
				http.NotFound(w, r)
				return
			}
			b, err := os.ReadFile(p)
			if err != nil {
				http.NotFound(w, r)
				return
			}
			sum := sha256.Sum256(b)
			if hex.EncodeToString(sum[:]) != v.Hash {
				JSON(w, 409, map[string]string{"error": "artifact checksum mismatch"})
				return
			}
			w.Header().Set("Content-Type", "application/octet-stream")
			w.Header().Set("Content-Disposition", "attachment; filename=artifact.parquet")
			w.Write(b)
			return
		}
		http.NotFound(w, r)
	})
}
