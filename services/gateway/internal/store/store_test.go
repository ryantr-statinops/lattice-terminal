package store

import (
	"encoding/json"
	"testing"
)

func TestIdempotencyAndRecovery(t *testing.T) {
	root := t.TempDir()
	s, err := Open(root)
	if err != nil {
		t.Fatal(err)
	}
	r := Run{ID: "r", Kind: "research", File: "x.py", Snapshot: "hash", Params: json.RawMessage(`{}`)}
	if err = s.CreateRun(r); err != nil {
		t.Fatal(err)
	}
	e := Event{Seq: 1, Type: "state", Payload: json.RawMessage(`{}`)}
	if err = s.Append("r", e, "running"); err != nil {
		t.Fatal(err)
	}
	if err = s.Append("r", e, "completed"); err != nil {
		t.Fatal(err)
	}
	v, _ := s.Run("r")
	if v.Status != "running" {
		t.Fatal("duplicate changed state")
	}
	s.Close()
	s, err = Open(root)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	v, _ = s.Run("r")
	if v.Status != "interrupted" {
		t.Fatal(v.Status)
	}
}
