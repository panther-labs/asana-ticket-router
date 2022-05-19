import pytest

from productivity.ephemeral_statistics.ephemeral_statistics import EphemeralStatistics


@pytest.mark.manual_test
def test_manual():
    EphemeralStatistics.add_test_role("ephemeral_admin", "root-ephemeral-deployment-admin", "us-west-2")
    print(EphemeralStatistics().main())
