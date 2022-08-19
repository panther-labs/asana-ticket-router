package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"

	"github.com/DataDog/datadog-api-client-go/v2/api/datadog"
	"github.com/DataDog/datadog-api-client-go/v2/api/datadogV1"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
)

type API struct {
	datadogCtx   context.Context
	datadogEvent *datadogV1.EventsApi
	secretToken  []byte
}

type Tag struct {
	Tag string

	Major      uint64
	Minor      uint64
	Patch      uint64
	Prerelease string
}

func SetupAPI() (*API, error) {
	datadogSecret, err := loadSecret("DATADOG_SECRET_ARN")
	if err != nil {
		return nil, err
	}
	githubSecret, err := loadSecret("GITHUB_SECRET_ARN")
	if err != nil {
		return nil, err
	}

	ctx := context.WithValue(
		context.Background(),
		datadog.ContextAPIKeys,
		map[string]datadog.APIKey{
			"apiKeyAuth": {
				Key: *datadogSecret,
			},
			//            "appKeyAuth": {
			//                Key: os.Getenv("DD_CLIENT_APP_KEY"),
			//            },
		},
	)

	configuration := datadog.NewConfiguration()
	apiClient := datadog.NewAPIClient(configuration)
	events := datadogV1.NewEventsApi(apiClient)

	return &API{
		datadogCtx:   ctx,
		datadogEvent: events,
		secretToken:  []byte(*githubSecret),
	}, nil
}

// Lifted from ephemeral (something something shared private go libraries)
func (x *API) Handler(ctx context.Context, in json.RawMessage) (events.APIGatewayV2HTTPResponse, error) {
	var req events.APIGatewayV2HTTPRequest
	err := json.Unmarshal(in, &req)
	if err != nil {
		fmt.Printf("error parsing input: %v\n", err)
		return internalError(), err
	}

	event, err := x.parseWebhook(req)
	if err != nil {
		fmt.Println(err.Error())
		return badInput(), nil
	}

	tag, err := processEvent(event)
	if err != nil {
		fmt.Printf("error handling event: %v", err)
		return internalError(), nil
	}

	// Datadog metrics
	fmt.Println(tag)

	return noContent(), nil
}

func main() {
	api, err := SetupAPI()
	if err != nil {
		log.Fatalf("failed to setup, %v", err)
	}

	lambda.Start(api.Handler)
}
