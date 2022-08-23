package main

import (
	"encoding/json"
	"fmt"
	"testing"

	"github.com/google/go-github/v42/github"
	"github.com/stretchr/testify/require"
)

func TestProcess(t *testing.T) {
	tests := []struct {
		Name     string
		Input    string
		Expected *Tag
	}{
		{
			"Tag",
			`{"ref": "v1.40.14","ref_type": "tag"}`,
			&Tag{"v1.40.14", 1, 40, 14, ""},
		},
		{
			"RC",
			`{"ref": "v1.41.0-RC-7967-2022-08-19T19-07-00","ref_type": "tag"}`,
			&Tag{"v1.41.0-RC-7967-2022-08-19T19-07-00", 1, 41, 0, "RC-7967-2022-08-19T19-07-00"},
		},
		{
			"Other",
			`{"ref": "test-automation","ref_type": "tag"}`,
			nil,
		},
	}

	for _, r := range tests {
		var create github.CreateEvent
		err := json.Unmarshal([]byte(r.Input), &create)
		require.NoError(t, err, fmt.Sprintf("%s failed to unmarshal input", r.Name))

		result, err := processEvent(&create)
		require.NoError(t, err, fmt.Sprintf("%s failed to process input", r.Name))
		if r.Expected == nil {
			require.Nil(t, result, r.Name)
		} else {
			require.NotNil(t, result, fmt.Sprintf("%s output is empty", r.Name))
			require.Equal(t, *r.Expected, *result, r.Name)
		}
	}
}
