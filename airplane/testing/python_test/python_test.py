# Linked to https://app.airplane.dev/t/python_test [do not edit this line]
from pyshared.aws_creds import get_credentialed_client


def main(params):
    customer_role_arn = f"arn:aws:iam::421952789667:role/PantherSupportRole-us-east-1"

    sts_client = get_credentialed_client(service_name="sts",
                                         arns=("arn:aws:iam::255674391660:role/CustomerSupport", customer_role_arn),
                                         desc="testing",
                                         region="us-east-1")
    print(sts_client.get_caller_identity())
