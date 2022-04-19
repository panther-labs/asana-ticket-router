from pyshared.aws_consts import get_aws_const


class HostedOrgs:
    CUSTOMER = get_aws_const("HOSTED_CUSTOMER_OU_ID")
    TERMINATED = get_aws_const("HOSTED_TERMINATED_OU_ID")

    _OU_NAME_DICT = {
        "customer": CUSTOMER,
        "terminated": TERMINATED,
    }

    @classmethod
    def get_ou_id(cls, ou_name: str) -> str:
        if ou_name not in cls._OU_NAME_DICT:
            raise AttributeError(f"OU '{ou_name}' is not available.")
        return cls._OU_NAME_DICT[ou_name]
