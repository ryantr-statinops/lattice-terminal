package api

import (
	"encoding/json"
	"kestrel-terminal/gateway/internal/store"
	"kestrel-terminal/gateway/internal/workspace"
	"os"
	"path/filepath"
	"testing"
)

func TestFrozenTrainRejectsChangedHelpersAndCapital(t *testing.T) {
	root := t.TempDir()
	repo := t.TempDir()
	os.MkdirAll(filepath.Join(repo, "services", "engine"), 0700)
	os.WriteFile(filepath.Join(repo, "services", "engine", "uv.lock"), []byte("lock"), 0600)
	db, err := store.Open(root)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	w := workspace.Workspace{Root: root, Repository: repo}
	w.Write("backtest", "main.py", "KESTREL_KIND='backtest'\ndef run(context): pass", false)
	params := json.RawMessage(`{"stage":"train","capital":"1000"}`)
	snapshot, err := w.Snapshot("backtest", "main.py", params)
	if err != nil {
		t.Fatal(err)
	}
	db.CreateRun(store.Run{ID: "train", Kind: "backtest", File: "main.py", Snapshot: snapshot, Params: params})
	db.Append("train", store.Event{Seq: 1, Type: "state", Payload: json.RawMessage(`{}`)}, "running")
	db.Append("train", store.Event{Seq: 2, Type: "backtest_report", Payload: json.RawMessage(`{}`)}, "")
	db.Append("train", store.Event{Seq: 3, Type: "state", Payload: json.RawMessage(`{}`)}, "completed")
	a := API{Store: db, Workspace: w}
	test := json.RawMessage(`{"stage":"test","capital":"1000","train_run_id":"train"}`)
	current, _ := w.Snapshot("backtest", "main.py", test)
	if err = a.validateBacktest("backtest", current, test); err != nil {
		t.Fatal(err)
	}
	if a.validateBacktest("backtest", current, json.RawMessage(`{"stage":"test","capital":"2000","train_run_id":"train"}`)) == nil {
		t.Fatal("changed capital accepted")
	}
	w.Write("backtest", "helper.py", "future_data=True", false)
	changed, _ := w.Snapshot("backtest", "main.py", test)
	if a.validateBacktest("backtest", changed, test) == nil {
		t.Fatal("changed code accepted")
	}
}
