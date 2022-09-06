from dataclasses import dataclass
from re import sub
from coolname import generate_slug
from v2.exceptions import FairytaleNameAlreadyInUseException
from operations.name_generator.name_validator import NameValidator
from v2.task_models.airplane_task import AirplaneTask


@dataclass
class AirplaneParams:
    account_name: str
    deploy_group: str
    fairytale_name: str = ""
    customer_domain: str = ""


class NameGenerator(AirplaneTask):
    """
        Why pass in the fairytale name and just return it?
        So Airplane runbooks can use this task to standardize an output variable future blocks can use, whether a
        new name is generated or an existing one is used.
    """

    def __init__(self, params):
        self.ap_params = AirplaneParams(**params)
        self.domain_name_was_passed_in = bool(self.ap_params.customer_domain)
        self.fairytale_name_was_passed_in = bool(self.ap_params.fairytale_name)
        self.fairytale_name = self._generate_fairytale_name()
        self.domain_name = self._generate_domain_name()
        self.validator = None

    def _get_validator_instance(self):
        return self.validator if self.validator else NameValidator()

    def _generate_fairytale_name(self):
        return self.ap_params.fairytale_name if self.fairytale_name_was_passed_in else generate_slug(2)

    def _generate_domain_name(self):
        if self.domain_name_was_passed_in:
            if self.ap_params.deploy_group == "T":
                raise ValueError(
                    f"Customer Domain [{self.ap_params.customer_domain}] should not be set for trial SaaS account [{self.fairytale_name}]"
                )
            else:
                return f"{self.ap_params.customer_domain}.runpanther.net"
        else:
            prefix = self.fairytale_name if self.ap_params.deploy_group == "T" else self.ap_params.account_name
            domain_prefix = sub("[^0-9a-zA-Z-]+", "-", prefix).strip("-").lower()
            return f"{domain_prefix}.runpanther.net"

    def validate(self):
        try:
            self._get_validator_instance().run_validation(self.domain_name, self.fairytale_name)
        except FairytaleNameAlreadyInUseException as e:
            if self.fairytale_name_was_passed_in:
                raise e
            else:
                print(f"WARN: Generated Fairytale Name [{self.fairytale_name}] already exists. Generating new one!")
                self.fairytale_name = self._generate_fairytale_name()
                if self.ap_params.deploy_group == "T":
                    # Must regenerate domain name if for some reason fairytale exists
                    # and domain name was generated from fairytale
                    self.domain_name = self._generate_domain_name()
                self.validate()

    def get_failure_slack_channel(self):
        return "#triage-deployment"

    def run(self):
        self.validate()
        return {"fairytale_name": self.fairytale_name, "customer_domain": self.domain_name}


def main(params):
    return NameGenerator(params).run_notify_failures()
