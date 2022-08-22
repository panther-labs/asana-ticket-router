//go:build datadog
// +build datadog

package main

import (
	"os"
	"testing"

	"github.com/stretchr/testify/require"
)

func TestDatadog(t *testing.T) {
	key, ok := os.LookupEnv("TEST_DATADOG_API_KEY")
	require.True(t, ok, "apikey required")

	dd := SetupDatadog(key)

	tag := Tag{"v1.00.00", 1, 00, 00, "RC-test"}
	err := dd.PostMetrics(tag)
	require.NoError(t, err)
}
