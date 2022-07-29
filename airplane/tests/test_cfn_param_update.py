import pytest

from dataclasses import asdict

from operations.cfn_param_update.cfn_param_update import AirplaneParams, CfnParamUpdate, main

params = AirplaneParams(fairytale_name="tuscan-beagle",
                        cfn_param_key_vals="GraphAPITimeoutSeconds=30,OnboardSelf=true,SentryEnvironment=dev")


def test_param_parsing():
    parsed_params = CfnParamUpdate.parse_params(params)
    assert parsed_params.fairytale_name == "tuscan-beagle"
    assert parsed_params.cfn_params == {"GraphAPITimeoutSeconds": 30, "OnboardSelf": True, "SentryEnvironment": "dev"}


@pytest.mark.manual_test
def test_manual():
    main(asdict(params))
