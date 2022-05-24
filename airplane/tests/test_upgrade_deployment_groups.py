import pytest

from dataclasses import asdict

from operations.upgrade_deployment_groups.upgrade_deployment_groups import AirplaneParams, main


@pytest.mark.manual_test
def test_manual():
    params = AirplaneParams(deployment_groups="Z", version="9.9.9")
    main(asdict(params))
