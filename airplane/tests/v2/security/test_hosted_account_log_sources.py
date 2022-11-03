import pytest

from security.hosted_account_log_sources_airplane import HostedAccountLogSources

AWS_ACCOUNT_ID = "861926576627"
ONBOARD = False
ROLE_ARN = ""


@pytest.mark.manual_test
def test_manual():
    HostedAccountLogSources(aws_account_id=AWS_ACCOUNT_ID, onboard=ONBOARD).run()
