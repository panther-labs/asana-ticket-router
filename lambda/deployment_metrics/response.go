package main

import (
	"net/http"

	"github.com/aws/aws-lambda-go/events"
)

func noContent() events.APIGatewayV2HTTPResponse {
	return events.APIGatewayV2HTTPResponse{
		StatusCode: http.StatusNoContent,
	}
}

func internalError() events.APIGatewayV2HTTPResponse {
	return events.APIGatewayV2HTTPResponse{
		StatusCode: http.StatusInternalServerError,
	}
}

func badInput() events.APIGatewayV2HTTPResponse {
	return events.APIGatewayV2HTTPResponse{
		StatusCode: http.StatusBadRequest,
	}
}
