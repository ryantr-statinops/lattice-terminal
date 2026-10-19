package api

import "net/http"

func (a *API) fundRoutes(m *http.ServeMux) {
	m.HandleFunc("GET /api/v1/funds", func(w http.ResponseWriter, r *http.Request) {
		v, err := a.Store.Funds()
		if err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, v)
	})
	m.HandleFunc("POST /api/v1/funds", func(w http.ResponseWriter, r *http.Request) {
		var v struct {
			Name    string `json:"name"`
			Kind    string `json:"kind"`
			Capital string `json:"capital"`
			Key     string `json:"request_key"`
		}
		if !Read(w, r, &v) {
			return
		}
		id, err := a.Store.CreateFund(v.Name, v.Kind, v.Capital, v.Key)
		if err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 201, map[string]string{"id": id})
	})
	m.HandleFunc("POST /api/v1/funds/{id}/cash", func(w http.ResponseWriter, r *http.Request) {
		var v struct {
			Kind   string `json:"kind"`
			Amount string `json:"amount"`
			Key    string `json:"request_key"`
		}
		if !Read(w, r, &v) {
			return
		}
		if err := a.Store.CashFlow(r.PathValue("id"), v.Kind, v.Amount, v.Key); err != nil {
			Fail(w, err)
			return
		}
		w.WriteHeader(204)
	})
	m.HandleFunc("POST /api/v1/funds/{id}/allocations", func(w http.ResponseWriter, r *http.Request) {
		var v struct {
			Name   string `json:"name"`
			Mode   string `json:"mode"`
			Amount string `json:"amount"`
			Key    string `json:"request_key"`
		}
		if !Read(w, r, &v) {
			return
		}
		id, err := a.Store.Allocate(r.PathValue("id"), v.Name, v.Mode, v.Amount, v.Key)
		if err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 201, map[string]string{"id": id})
	})
	m.HandleFunc("POST /api/v1/funds/transfer", func(w http.ResponseWriter, r *http.Request) {
		var v struct {
			From   string `json:"from"`
			To     string `json:"to"`
			Amount string `json:"amount"`
			Key    string `json:"request_key"`
		}
		if !Read(w, r, &v) {
			return
		}
		if err := a.Store.Transfer(v.From, v.To, v.Amount, v.Key); err != nil {
			Fail(w, err)
			return
		}
		w.WriteHeader(204)
	})
	m.HandleFunc("GET /api/v1/allocations", func(w http.ResponseWriter, r *http.Request) {
		v, err := a.Store.Allocations()
		if err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, v)
	})
	m.HandleFunc("POST /api/v1/allocations/{id}/release", func(w http.ResponseWriter, r *http.Request) {
		var v struct {
			Amount string `json:"amount"`
			Key    string `json:"request_key"`
		}
		if !Read(w, r, &v) {
			return
		}
		if err := a.Store.Release(r.PathValue("id"), v.Amount, v.Key); err != nil {
			Fail(w, err)
			return
		}
		w.WriteHeader(204)
	})
	m.HandleFunc("GET /api/v1/positions", func(w http.ResponseWriter, r *http.Request) {
		v, err := a.Store.Positions()
		if err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, v)
	})
}
