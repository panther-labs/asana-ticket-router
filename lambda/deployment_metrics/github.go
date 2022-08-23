package main

import (
	"encoding/json"
	"fmt"
	"mime"
	"net/textproto"
	"strings"

	"github.com/Masterminds/semver/v3"
	"github.com/aws/aws-lambda-go/events"
	"github.com/google/go-github/v42/github"
)

func (x *API) parseWebhook(req events.APIGatewayV2HTTPRequest) (interface{}, error) {
	headers := make(map[string]string)
	for k, v := range req.Headers {
		headers[textproto.CanonicalMIMEHeaderKey(k)] = v
	}

	githubEventTypeHeader, ok := headers[github.EventTypeHeader]
	if !ok {
		return nil, fmt.Errorf("error loading github header\n")
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
		return nil, fmt.Errorf("Unable to parsing content-type: %v", err)
	}

	payload, err := github.ValidatePayloadFromBody(contentType, strings.NewReader(req.Body), signature, x.secretToken)
	if err != nil {

		return nil, fmt.Errorf("Unable to validate payload from body: %v", err)
	}

	// Parse payload
	event, err := github.ParseWebHook(githubEventTypeHeader, payload)
	if err != nil {
		return nil, fmt.Errorf("Unable to parse payload: %v", err)
	}

	return event, nil
}

func processEvent(event interface{}) (*Tag, error) {
	logPayload := func() {
		bytes, _ := json.Marshal(event)
		fmt.Println(string(bytes))
	}

	var tag *Tag
	var err error
	switch event := event.(type) {
	case *github.CreateEvent:
		logPayload()
		if *event.RefType == "tag" {
			tag = parseTag(*event.Ref)
		}
	case *github.PushEvent:
		logPayload()
	case *github.StatusEvent:
		logPayload()
	default:
		err = fmt.Errorf("Unhandled event type")
	}
	if err != nil {
		return nil, err
	}

	return tag, nil
}

func parseTag(tag string) *Tag {
	v, err := semver.NewVersion(tag)
	if err != nil {
		return nil
	}

	return &Tag{
		Tag:        tag,
		Major:      v.Major(),
		Minor:      v.Minor(),
		Patch:      v.Patch(),
		Prerelease: v.Prerelease(),
	}
}
