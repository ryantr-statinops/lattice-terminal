package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
)

func handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/v1/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"service": "kestrel-gateway", "status": "ok", "mode": "fixture-only"})
	})
	return mux
}
func main() {
	if err := http.ListenAndServe("127.0.0.1:8080", handler()); err != nil {
		log.Print(err)
		os.Exit(1)
	}
}
