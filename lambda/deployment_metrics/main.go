package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"mime"
	"net/textproto"
	"strings"

	"github.com/DataDog/datadog-api-client-go/v2/api/datadog"
	"github.com/DataDog/datadog-api-client-go/v2/api/datadogV1"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/google/go-github/v42/github"
)

type API struct {
	datadogCtx   context.Context
	datadogEvent *datadogV1.EventsApi
	secretToken  []byte
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

	headers := make(map[string]string)
	for k, v := range req.Headers {
		headers[textproto.CanonicalMIMEHeaderKey(k)] = v
	}

	githubEventTypeHeader, ok := headers[github.EventTypeHeader]
	if !ok {
		fmt.Printf("error loading github header: %v\n", err)
		return badInput(), nil
	}
	fmt.Printf("event_type: %s\n", githubEventTypeHeader)

	// Validate payload
	// https://github.com/google/go-github/blob/master/github/messages.go#L226-L238
	signature := headers[github.SHA256SignatureHeader]
	if signature == "" {
		signature = headers[github.SHA1SignatureHeader]
	}

	contentType, _, err := mime.ParseMediaType(headers["Content-Type"])
	if err != nil {
		fmt.Printf("Unable to parsing content-type: %v", err)
		return badInput(), nil
	}

	payload, err := github.ValidatePayloadFromBody(contentType, strings.NewReader(req.Body), signature, x.secretToken)
	if err != nil {
		fmt.Printf("Unable to validate payload from body: %v", err)
		return badInput(), nil
	}

	// Parse payload
	event, err := github.ParseWebHook(githubEventTypeHeader, payload)
	if err != nil {
		fmt.Printf("Unable to parse payload: %v", err)
		return badInput(), nil
	}
	err = x.processEvent(event)
	if err != nil {
		fmt.Printf("error handling event: %v", err)
		return internalError(), nil
	}

	return noContent(), nil
}

func (x *API) processEvent(event interface{}) error {
	logPayload := func() {
		bytes, _ := json.Marshal(event)
		fmt.Println(string(bytes))
	}

	var err error
	switch event.(type) {
	case *github.PushEvent:
		logPayload()
	case *github.StatusEvent:
		logPayload()
	default:
		err = fmt.Errorf("Unhandled event type")
	}
	if err != nil {
		return err
	}

	// Datadog metrics

	return nil
}

func main() {
	api, err := SetupAPI()
	if err != nil {
		log.Fatalf("failed to setup, %v", err)
	}

	lambda.Start(api.Handler)
}
