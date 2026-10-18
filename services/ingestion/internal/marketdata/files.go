package marketdata

import (
	"archive/zip"
	"bufio"
	"crypto/sha256"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"
)

func LoadArchiveFile(path, checksumPath string, cfg ParseConfig) ([]Candle, InputObject, error) {
	if cfg.SourceID != SourceFixture {
		return nil, InputObject{}, errors.New("offline ingestion accepts synthetic fixture inputs only")
	}
	hash, err := hashFile(path)
	if err != nil {
		return nil, InputObject{}, err
	}
	cfg.SourceObjectID = hash
	if strings.EqualFold(filepath.Ext(path), ".zip") {
		if checksumPath == "" {
			checksumPath = path + ".CHECKSUM"
		}
		if err := verifyChecksum(checksumPath, filepath.Base(path), hash); err != nil {
			return nil, InputObject{}, err
		}
	}
	if err := verifySyntheticFixture(path, hash); err != nil {
		return nil, InputObject{}, err
	}
	file, err := os.Open(path)
	if err != nil {
		return nil, InputObject{}, errors.New("cannot open local archive input")
	}
	defer file.Close()
	var candles []Candle
	if strings.EqualFold(filepath.Ext(path), ".zip") {
		info, err := file.Stat()
		if err != nil {
			return nil, InputObject{}, err
		}
		archive, err := zip.NewReader(file, info.Size())
		if err != nil {
			return nil, InputObject{}, fmt.Errorf("invalid local archive zip: %w", err)
		}
		var csvFile *zip.File
		for _, candidate := range archive.File {
			if !candidate.FileInfo().IsDir() && strings.EqualFold(filepath.Ext(candidate.Name), ".csv") {
				if csvFile != nil {
					return nil, InputObject{}, errors.New("archive zip must contain exactly one CSV file")
				}
				csvFile = candidate
			}
		}
		if csvFile == nil {
			return nil, InputObject{}, errors.New("archive zip contains no CSV file")
		}
		if csvFile.UncompressedSize64 > 1<<30 {
			return nil, InputObject{}, errors.New("archive CSV exceeds 1 GiB safety limit")
		}
		csvReader, err := csvFile.Open()
		if err != nil {
			return nil, InputObject{}, err
		}
		candles, err = ParseArchiveCSV(csvReader, cfg)
		closeErr := csvReader.Close()
		if err != nil {
			return nil, InputObject{}, err
		}
		if closeErr != nil {
			return nil, InputObject{}, closeErr
		}
	} else {
		candles, err = ParseArchiveCSV(bufio.NewReader(file), cfg)
	}
	if err != nil {
		return nil, InputObject{}, err
	}
	return candles, inputObject(path, cfg.SourceID, hash, cfg.TimestampUnit, cfg.RetrievedAt), nil
}

func LoadRESTFile(path string, cfg ParseConfig) ([]Candle, InputObject, error) {
	if cfg.SourceID != SourceFixture {
		return nil, InputObject{}, errors.New("offline ingestion accepts synthetic fixture inputs only")
	}
	hash, err := hashFile(path)
	if err != nil {
		return nil, InputObject{}, err
	}
	cfg.SourceObjectID = hash
	if err := verifySyntheticFixture(path, hash); err != nil {
		return nil, InputObject{}, err
	}
	file, err := os.Open(path)
	if err != nil {
		return nil, InputObject{}, errors.New("cannot open local REST fixture input")
	}
	defer file.Close()
	candles, err := ParseRESTKlines(file, cfg)
	if err != nil {
		return nil, InputObject{}, err
	}
	return candles, inputObject(path, cfg.SourceID, hash, cfg.TimestampUnit, cfg.RetrievedAt), nil
}

type syntheticFixtureEvidence struct {
	SchemaVersion string `json:"schema_version"`
	IsSynthetic bool `json:"is_synthetic"`
	SourceID string `json:"source_id"`
	SHA256 string `json:"sha256"`
}

func verifySyntheticFixture(path, actualHash string) error {
	marker, err := os.Open(path + ".fixture.json")
	if err != nil {
		return errors.New("offline mode requires a tracked synthetic fixture evidence file")
	}
	defer marker.Close()
	var evidence syntheticFixtureEvidence
	decoder := json.NewDecoder(marker)
	if err := decoder.Decode(&evidence); err != nil {
		return errors.New("invalid synthetic fixture evidence")
	}
	var extra any
	if err := decoder.Decode(&extra); err != io.EOF {
		return errors.New("synthetic fixture evidence must contain one JSON document")
	}
	if evidence.SchemaVersion != SchemaVersion || !evidence.IsSynthetic || evidence.SourceID != SourceFixture || !strings.EqualFold(evidence.SHA256, actualHash) {
		return errors.New("input is not an approved synthetic fixture or its hash changed")
	}
	return nil
}

func inputObject(path, sourceID, hash string, unit TimestampUnit, retrievedAt time.Time) InputObject {
	return InputObject{SourceID: sourceID, ObjectID: hash, SHA256: hash, TimestampUnit: unit, RetrievedAt: retrievedAt.UTC(), InputPath: filepath.Base(path), syntheticVerified: true}
}

func hashFile(path string) (string, error) {
	file, err := os.Open(path)
	if err != nil {
		return "", errors.New("cannot open local input file")
	}
	defer file.Close()
	hash := sha256.New()
	if _, err := io.Copy(hash, file); err != nil {
		return "", fmt.Errorf("cannot hash local input: %w", err)
	}
	return hex.EncodeToString(hash.Sum(nil)), nil
}

func verifyChecksum(checksumPath, filename, actualHash string) error {
	file, err := os.Open(checksumPath)
	if err != nil {
		return errors.New("archive checksum file is required")
	}
	defer file.Close()
	scanner := bufio.NewScanner(file)
	var expected string
	for scanner.Scan() {
		fields := strings.Fields(scanner.Text())
		if len(fields) == 0 {
			continue
		}
		if len(fields) > 1 && filepath.Base(strings.TrimPrefix(fields[1], "*")) != filename {
			continue
		}
		expected = strings.ToLower(fields[0])
		break
	}
	if err := scanner.Err(); err != nil {
		return err
	}
	if len(expected) != 64 || expected != strings.ToLower(actualHash) {
		return errors.New("archive SHA-256 checksum mismatch")
	}
	return nil
}
