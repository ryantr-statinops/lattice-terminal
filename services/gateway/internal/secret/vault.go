package secret

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"errors"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"time"

	"kestrel-terminal/gateway/internal/fileutil"
)

const (
	vaultFileVersion = 1
	maxVaultFileSize = 16 * 1024 * 1024
	maxSecretSize    = 1024 * 1024
)

var vaultIDPattern = regexp.MustCompile(`^[a-z0-9][a-z0-9._-]{0,63}$`)

type encryptedRecord struct {
	Nonce      string `json:"nonce"`
	Ciphertext string `json:"ciphertext"`
	UpdatedAt  string `json:"updated_at"`
}

type vaultDocument struct {
	Version int                        `json:"version"`
	Records map[string]encryptedRecord `json:"records"`
}

// Vault stores provider credentials encrypted with the key held by the OS keyring.
// Its files live outside the directories included in ordinary application backups.
type Vault struct {
	mu   sync.Mutex
	path string
	aead cipher.AEAD
}

func newVault(root string, key []byte) (*Vault, error) {
	if len(key) != 32 {
		return nil, errors.New("vault master key must be 32 bytes")
	}
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, errors.New("could not initialize credential vault")
	}
	aead, err := cipher.NewGCM(block)
	if err != nil {
		return nil, errors.New("could not initialize credential vault")
	}
	root, err = filepath.Abs(root)
	if err != nil {
		return nil, errors.New("could not resolve credential vault path")
	}
	return &Vault{path: filepath.Join(root, "provider-vault", "credentials.json"), aead: aead}, nil
}

func ValidVaultID(value string) bool { return vaultIDPattern.MatchString(value) }

func vaultRecordKey(provider, service string) string { return provider + "/" + service }

func vaultAAD(provider, service string) []byte {
	return []byte("kestrel.provider-credential.v1\x00" + provider + "\x00" + service)
}

func (v *Vault) read() (vaultDocument, error) {
	doc := vaultDocument{Version: vaultFileVersion, Records: map[string]encryptedRecord{}}
	b, err := os.ReadFile(v.path)
	if os.IsNotExist(err) {
		return doc, nil
	}
	if err != nil {
		return vaultDocument{}, errors.New("could not read credential vault")
	}
	if len(b) > maxVaultFileSize {
		return vaultDocument{}, errors.New("credential vault exceeds size limit")
	}
	decoder := json.NewDecoder(strings.NewReader(string(b)))
	decoder.DisallowUnknownFields()
	if err = decoder.Decode(&doc); err != nil || doc.Version != vaultFileVersion || doc.Records == nil {
		return vaultDocument{}, errors.New("credential vault format is invalid")
	}
	var trailing any
	if err = decoder.Decode(&trailing); err != io.EOF {
		return vaultDocument{}, errors.New("credential vault format is invalid")
	}
	if len(doc.Records) > 1000 {
		return vaultDocument{}, errors.New("credential vault has too many records")
	}
	return doc, nil
}

func (v *Vault) write(doc vaultDocument) error {
	if len(doc.Records) > 1000 {
		return errors.New("credential vault has too many records")
	}
	if err := os.MkdirAll(filepath.Dir(v.path), 0700); err != nil {
		return errors.New("could not create credential vault directory")
	}
	b, err := json.Marshal(doc)
	if err != nil || len(b) > maxVaultFileSize {
		return errors.New("credential vault exceeds size limit")
	}
	tmp, err := os.CreateTemp(filepath.Dir(v.path), ".credentials-*.tmp")
	if err != nil {
		return errors.New("could not prepare credential vault update")
	}
	tmpPath := tmp.Name()
	defer os.Remove(tmpPath)
	if err = tmp.Chmod(0600); err == nil {
		_, err = tmp.Write(b)
	}
	if err == nil {
		err = tmp.Sync()
	}
	closeErr := tmp.Close()
	if err == nil {
		err = closeErr
	}
	if err != nil {
		return errors.New("could not write credential vault")
	}
	if err = fileutil.Rename(tmpPath, v.path); err != nil {
		return errors.New("could not publish credential vault")
	}
	return nil
}

// Set encrypts one JSON credential document and atomically persists the vault.
func (v *Vault) Set(provider, service string, plaintext []byte) error {
	if !ValidVaultID(provider) || !ValidVaultID(service) || len(plaintext) == 0 || len(plaintext) > maxSecretSize || !json.Valid(plaintext) {
		return errors.New("invalid provider credential")
	}
	v.mu.Lock()
	defer v.mu.Unlock()
	doc, err := v.read()
	if err != nil {
		return err
	}
	nonce := make([]byte, v.aead.NonceSize())
	if _, err = rand.Read(nonce); err != nil {
		return errors.New("could not encrypt provider credential")
	}
	ciphertext := v.aead.Seal(nil, nonce, plaintext, vaultAAD(provider, service))
	doc.Records[vaultRecordKey(provider, service)] = encryptedRecord{
		Nonce:      base64.StdEncoding.EncodeToString(nonce),
		Ciphertext: base64.StdEncoding.EncodeToString(ciphertext),
		UpdatedAt:  time.Now().UTC().Format(time.RFC3339Nano),
	}
	return v.write(doc)
}

// Get returns a decrypted copy of one credential document.
func (v *Vault) Get(provider, service string) ([]byte, error) {
	if !ValidVaultID(provider) || !ValidVaultID(service) {
		return nil, errors.New("invalid provider credential reference")
	}
	v.mu.Lock()
	defer v.mu.Unlock()
	doc, err := v.read()
	if err != nil {
		return nil, err
	}
	record, ok := doc.Records[vaultRecordKey(provider, service)]
	if !ok {
		return nil, os.ErrNotExist
	}
	nonce, nonceErr := base64.StdEncoding.DecodeString(record.Nonce)
	ciphertext, cipherErr := base64.StdEncoding.DecodeString(record.Ciphertext)
	if nonceErr != nil || cipherErr != nil || len(nonce) != v.aead.NonceSize() {
		return nil, errors.New("provider credential record is invalid")
	}
	plaintext, err := v.aead.Open(nil, nonce, ciphertext, vaultAAD(provider, service))
	if err != nil || !json.Valid(plaintext) {
		return nil, errors.New("provider credential could not be decrypted")
	}
	return plaintext, nil
}

// HasProvider reports whether the encrypted vault contains any service record
// for a provider without decrypting or returning credential values.
func (v *Vault) HasProvider(provider string) (bool, error) {
	if !ValidVaultID(provider) {
		return false, errors.New("invalid provider credential reference")
	}
	v.mu.Lock()
	defer v.mu.Unlock()
	doc, err := v.read()
	if err != nil {
		return false, err
	}
	prefix := provider + "/"
	for reference := range doc.Records {
		if strings.HasPrefix(reference, prefix) {
			return true, nil
		}
	}
	return false, nil
}

// Delete removes one credential record and atomically persists the vault.
func (v *Vault) Delete(provider, service string) error {
	if !ValidVaultID(provider) || !ValidVaultID(service) {
		return errors.New("invalid provider credential reference")
	}
	v.mu.Lock()
	defer v.mu.Unlock()
	doc, err := v.read()
	if err != nil {
		return err
	}
	key := vaultRecordKey(provider, service)
	if _, ok := doc.Records[key]; !ok {
		return os.ErrNotExist
	}
	delete(doc.Records, key)
	return v.write(doc)
}
