package main

import (
	"context"
	"fmt"
	"os"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/secretsmanager"
)

func loadSecret(name string) (*string, error) {
	ctx := context.TODO()
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to load configuration, %w", err)
	}

	arn, ok := os.LookupEnv(name)
	if !ok {
		return nil, fmt.Errorf("missing required env '%s'", name)
	}

	client := secretsmanager.NewFromConfig(cfg)
	secret, err := client.GetSecretValue(ctx, &secretsmanager.GetSecretValueInput{
		SecretId: aws.String(arn),
	})
	if err != nil {
		return nil, fmt.Errorf("loading '%s': %w", name, err)
	}

	if secret.SecretString == nil {
		return nil, fmt.Errorf("unexpected empty secret string '%s'", name)
	}

	if *secret.SecretString == "" {
		return nil, fmt.Errorf("unexpected empty secret value '%s'", name)
	}

	return secret.SecretString, nil
}
