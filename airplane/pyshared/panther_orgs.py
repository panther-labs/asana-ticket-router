from pyshared.aws_consts import get_aws_const


class _PantherOrg:
    _OU_NAME_DICT = {}

    @classmethod
    def get_ou_id(cls, ou_name: str) -> str:
        if ou_name not in cls._OU_NAME_DICT:
            raise AttributeError(f"OU '{ou_name}' is not available.")
        return cls._OU_NAME_DICT[ou_name]


class RootOrg(_PantherOrg):
    NAME = "root"

    DEV_ACCOUNTS = get_aws_const("ROOT_DEV_ACCOUNTS_OU_ID")
    TERMINATED = get_aws_const("ROOT_TERMINATED_OU_ID")
    SUSPENDED = get_aws_const("ROOT_SUSPENDED_OU_ID")
    STAGING = get_aws_const("ROOT_STAGING_OU_ID")

    _OU_NAME_DICT = {
        "dev-accounts": DEV_ACCOUNTS,
        "terminated": TERMINATED,
        "suspended": SUSPENDED,
        "staging": STAGING,
    }


class HostedOrg(_PantherOrg):
    NAME = "hosted"

    CUSTOMER = get_aws_const("HOSTED_CUSTOMER_OU_ID")
    TERMINATED = get_aws_const("HOSTED_TERMINATED_OU_ID")
    SUSPENDED = get_aws_const("HOSTED_SUSPENDED_OU_ID")

    _OU_NAME_DICT = {
        "customer": CUSTOMER,
        "terminated": TERMINATED,
        "suspended": SUSPENDED,
    }


def get_panther_ou_id(organization: str, ou_name: str) -> str:
    if organization == RootOrg.NAME:
        panther_org = RootOrg
    elif organization == HostedOrg.NAME:
        panther_org = HostedOrg
    else:
        raise AttributeError(f"Organization {organization} doesn't exist.")
    return panther_org.get_ou_id(ou_name)
