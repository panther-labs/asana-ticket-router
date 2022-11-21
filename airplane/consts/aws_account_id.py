class AccountName:
    HOSTED_OPS = "hosted-ops"
    HOSTED_ROOT = "hosted-root"
    PANTHER_ROOT = "panther-root"


class AccountId:
    HOSTED_OPS = "246537256134"
    HOSTED_ROOT = "255674391660"
    PANTHER_ROOT = "292442345278"

    def __init__(self, account_name: str):
        self.account_id = {
            AccountName.HOSTED_OPS: AccountId.HOSTED_OPS,
            AccountName.HOSTED_ROOT: AccountId.HOSTED_ROOT,
            AccountName.PANTHER_ROOT: AccountId.PANTHER_ROOT
        }[account_name]
