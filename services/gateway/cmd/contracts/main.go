// Generates JSON Schema for exported gateway response DTOs. HTTP route coverage
// is tracked separately; this does not claim to be a complete external OpenAPI.
package main

import (
	"encoding/json"
	"fmt"
	"kestrel-terminal/gateway/internal/store"
	"os"
	"reflect"
	"strings"
)

func schema(t reflect.Type) any {
	if t == reflect.TypeOf(json.RawMessage{}) {
		return map[string]any{"type": "object"}
	}
	if t.Kind() == reflect.Pointer {
		return map[string]any{"anyOf": []any{schema(t.Elem()), map[string]string{"type": "null"}}}
	}
	switch t.Kind() {
	case reflect.Struct:
		p := map[string]any{}
		required := []string{}
		for i := 0; i < t.NumField(); i++ {
			f := t.Field(i)
			if f.Anonymous {
				nested := schema(f.Type).(map[string]any)
				for k, v := range nested["properties"].(map[string]any) {
					p[k] = v
				}
				required = append(required, nested["required"].([]string)...)
				continue
			}
			name := strings.Split(f.Tag.Get("json"), ",")[0]
			if name == "" {
				name = f.Name
			}
			if name == "-" {
				continue
			}
			p[name] = schema(f.Type)
			required = append(required, name)
		}
		return map[string]any{"type": "object", "properties": p, "required": required, "additionalProperties": false}
	case reflect.Slice:
		return map[string]any{"type": "array", "items": schema(t.Elem())}
	case reflect.Int, reflect.Int64:
		return map[string]string{"type": "integer"}
	case reflect.Bool:
		return map[string]string{"type": "boolean"}
	default:
		return map[string]string{"type": "string"}
	}
}
func main() {
	defs := map[string]any{}
	for _, v := range []any{store.Run{}, store.Event{}, store.Artifact{}, store.Fund{}, store.Allocation{}, store.PositionValue{}, store.FundValue{}, store.RecordedTrade{}, store.ImportPreview{}, store.PaperOrder{}, store.PaperFill{}} {
		t := reflect.TypeOf(v)
		defs[t.Name()] = schema(t)
	}
	b, err := json.MarshalIndent(map[string]any{"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "Kestrel gateway response DTOs", "$defs": defs}, "", "  ")
	if err != nil {
		panic(err)
	}
	b = append(b, '\n')
	fmt.Print(string(b))
	if len(os.Args) > 1 {
		panic("no arguments supported; redirect stdout to contracts/gateway.schema.json")
	}
}
