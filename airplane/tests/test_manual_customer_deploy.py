import pytest

from dataclasses import asdict

from operations.manual_deploys.manual_customer_deploy import AirplaneParams, main


@pytest.mark.manual_test
def test_manual():
    params = AirplaneParams(fairytale_name="tangible-dinosaur")
    main(asdict(params))
