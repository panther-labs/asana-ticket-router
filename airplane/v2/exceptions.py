class DuplicateAwsAccountIdException(Exception):
    pass


class DuplicateNotionFairytaleNameException(Exception):

    def __init__(self, fairytale_name, *args, **kwargs):
        msg = f"Fairytale name '{fairytale_name}' is found multiple times in the Panther Notion deploys page."
        super().__init__(msg, *args, **kwargs)


class InvalidFairytaleNameException(Exception):

    def __init__(self, fairytale_name, *args, **kwargs):
        msg = f"Fairytale name '{fairytale_name}' is not found."
        super().__init__(msg, *args, **kwargs)


class InvalidRegionException(Exception):

    def __init__(self, region, aws_account_id, *args, **kwargs):
        msg = f"No accounts use region '{region}' with AWS account ID of '{aws_account_id}'"
        super().__init__(msg, *args, **kwargs)
