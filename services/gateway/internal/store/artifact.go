package store

import (
	"io/fs"
	"regexp"
	"strings"
)

type Artifact struct {
	Name string `json:"name"`
	Path string `json:"path"`
	Hash string `json:"sha256"`
}

var digestPattern = regexp.MustCompile(`^[a-f0-9]{64}$`)

func validArtifact(run string, v Artifact) bool {
	return digestPattern.MatchString(run) && digestPattern.MatchString(v.Hash) && fs.ValidPath(v.Name) && !strings.ContainsAny(v.Name, "/:\\") && v.Path == "artifacts/"+run+"/"+v.Name
}
func (s *Store) Artifacts(run string) ([]Artifact, error) {
	rows, err := s.DB.Query("SELECT name,path,hash FROM artifacts WHERE run_id=? ORDER BY name", run)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	values := []Artifact{}
	for rows.Next() {
		var v Artifact
		if err = rows.Scan(&v.Name, &v.Path, &v.Hash); err != nil {
			return nil, err
		}
		values = append(values, v)
	}
	return values, rows.Err()
}
