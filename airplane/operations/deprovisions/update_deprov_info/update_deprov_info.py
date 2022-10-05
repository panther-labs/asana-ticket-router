from dataclasses import dataclass, fields
from datetime import datetime
import json

from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client
from pyshared.deprov_info import DeprovInfo
from v2.task_models.airplane_task import AirplaneTask


@dataclass(kw_only=True)
class AirplaneParams(DeprovInfo):
    fairytale_name: str


class DeprovInfoUpdater(AirplaneTask):

    def __init__(self):
        super().__init__()
        self.ap_params = None
        self.lambda_func = None
        self.client_descr = None
        self.role = None

    def run(self, params: dict):
        self.ap_params = AirplaneParams(**params)
        self._setup_aws_vars()
        self._get_client().invoke(FunctionName=self.lambda_func,
                                  Payload=json.dumps(self._construct_payload()),
                                  InvocationType="Event")

    def _get_client(self):
        return get_credentialed_client(service_name="lambda", arns=self.role, desc=self.client_descr)

    def _setup_aws_vars(self):
        prefix = "HOSTED" if self.ap_params.organization == "hosted" else "STAGING"
        self.lambda_func = get_aws_const(f"{prefix}_METADATA_UPDATE_LAMBDA")
        self.client_descr = f"{self.ap_params.fairytale_name}_update_deprov_info"
        self.role = get_aws_const(f"{prefix}_METADATA_UPDATE_ROLE")

    def _construct_payload(self):
        payload = {
            "item": {
                "CustomerId": self.ap_params.fairytale_name,
                "EventSource": "internal",
                "Updated": datetime.today().strftime("%Y-%m-%dT%H:%M:%S")
            },
            "type": "deployment-metadata"
        }
        for field in fields(self.ap_params):
            if field.name != "fairytale_name" and getattr(self.ap_params, field.name) is not None:
                payload["item"].setdefault("DeprovisionStatus", {})[field.name] = getattr(self.ap_params, field.name)

        return payload


def main(params):
    return DeprovInfoUpdater().run(params)
