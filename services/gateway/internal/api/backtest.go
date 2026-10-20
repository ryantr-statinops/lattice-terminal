package api

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
)

type codeManifest struct {
	Entry  string            `json:"entry"`
	Files  map[string]string `json:"files"`
	Lock   string            `json:"dependency_lock"`
	Engine string            `json:"engine_sha256"`
}

func (a *API) manifest(id string) (codeManifest, error) {
	var v codeManifest
	raw, err := os.ReadFile(filepath.Join(a.Workspace.Root, "code-snapshots", id, "manifest.json"))
	if err != nil {
		return v, err
	}
	sum := sha256.Sum256(raw)
	if hex.EncodeToString(sum[:]) != id {
		return v, errors.New("code snapshot checksum mismatch")
	}
	err = json.Unmarshal(raw, &v)
	return v, err
}
func (a *API) validateBacktest(kind, snapshot string, raw json.RawMessage) error {
	if kind != "backtest" {
		return nil
	}
	var params map[string]any
	if json.Unmarshal(raw, &params) != nil {
		return errors.New("invalid backtest config")
	}
	if params["stage"] != "test" {
		return nil
	}
	id, ok := params["train_run_id"].(string)
	if !ok || id == "" {
		return errors.New("Test requires a completed Train run")
	}
	train, err := a.Store.Run(id)
	if err != nil || train.Kind != "backtest" || train.Status != "completed" {
		return errors.New("baseline Train run is not completed")
	}
	var original map[string]any
	if json.Unmarshal(train.Params, &original) != nil || original["stage"] != "train" {
		return errors.New("baseline is not a Train run")
	}
	for _, key := range []string{"stage", "train_run_id", "timeout_seconds", "kind_detection"} {
		delete(params, key)
		delete(original, key)
	}
	left, _ := json.Marshal(params)
	right, _ := json.Marshal(original)
	if string(left) != string(right) {
		return errors.New("Test config differs from frozen Train parameters")
	}
	old, err := a.manifest(train.Snapshot)
	if err != nil {
		return err
	}
	current, err := a.manifest(snapshot)
	if err != nil {
		return err
	}
	x, _ := json.Marshal(old)
	y, _ := json.Marshal(current)
	if string(x) != string(y) {
		return errors.New("code/helpers/dependency lock changed; restore Train code or create a new Train run")
	}
	after := int64(0)
	for {
		events, err := a.Store.Events(id, after)
		if err != nil {
			return err
		}
		if len(events) == 0 {
			break
		}
		for _, event := range events {
			after = event.Seq
			if event.Type == "backtest_report" {
				return nil
			}
		}
	}
	return errors.New("baseline Train has no verified backtest report")
}
