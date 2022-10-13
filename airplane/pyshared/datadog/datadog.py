from datadog_api_client import ApiClient, Configuration


class Datadog():
    def __init__(self, api_key):
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        self.client = ApiClient(configuration)
