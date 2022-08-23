package main

import (
	"context"
	"fmt"
	"time"

	"github.com/DataDog/datadog-api-client-go/v2/api/datadog"
	"github.com/DataDog/datadog-api-client-go/v2/api/datadogV2"
)

type Datadog struct {
	Context context.Context
	Client  *datadog.APIClient
}

func SetupDatadog(apiKey string) *Datadog {
	ctx := context.WithValue(
		context.Background(),
		datadog.ContextAPIKeys,
		map[string]datadog.APIKey{
			"apiKeyAuth": {
				Key: apiKey,
			},
			//            "appKeyAuth": {
			//                Key: os.Getenv("DD_CLIENT_APP_KEY"),
			//            },
		},
	)

	configuration := datadog.NewConfiguration()
	apiClient := datadog.NewAPIClient(configuration)

	return &Datadog{
		Context: ctx,
		Client:  apiClient,
	}

}

func (x *Datadog) PostMetrics(t Tag) error {
	tags := []string{
		t.Tag,
		fmt.Sprintf("v%v.%v", t.Major, t.Minor),
		fmt.Sprintf("version:v%v.%v", t.Major, t.Minor),
	}

	if t.Prerelease != "" {
		tags = append(tags, "RC")
	}

	api := datadogV2.NewMetricsApi(x.Client)
	_, _, err := api.SubmitMetrics(x.Context, datadogV2.MetricPayload{
		Series: []datadogV2.MetricSeries{
			{
				Metric: "deployment.metrics.versions",
				Type:   datadogV2.METRICINTAKETYPE_COUNT.Ptr(),
				Points: []datadogV2.MetricPoint{
					{
						Timestamp: datadog.PtrInt64(time.Now().Unix()),
						Value:     datadog.PtrFloat64(1),
					},
				},
				Resources: []datadogV2.MetricResource{
					{
						Name: datadog.PtrString("enterprise"),
						Type: datadog.PtrString("version"),
					},
				},
				Tags: tags,
			},
		},
	}, *datadogV2.NewSubmitMetricsOptionalParameters())

	return err
}
