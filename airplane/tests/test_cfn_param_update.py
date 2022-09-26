import copy
import pytest

from dataclasses import asdict

from v2.exceptions import InvalidSalesPhaseChange
from operations.cfn_param_update.cfn_param_update import AirplaneParams, CfnParamUpdate, main

params = AirplaneParams(fairytale_name="tuscan-beagle",
                        cfn_param_key_vals="GraphAPITimeoutSeconds=30,OnboardSelf=true,SentryEnvironment=dev",
                        show_changes_only=True)


def test_param_parsing():
    parsed_params = CfnParamUpdate.parse_params(params)
    assert parsed_params.fairytale_name == "tuscan-beagle"
    assert parsed_params.cfn_params == {"GraphAPITimeoutSeconds": 30, "OnboardSelf": True, "SentryEnvironment": "dev"}


def test_return_val_shows_changed_values():
    old_cfg = {"key1": "val1", "key2": "val2", "key3": "val3"}
    new_cfg = {"key1": "new_val_1", "key3": "new_val_3", "key4": "val4"}
    return_val = CfnParamUpdate.gen_changed_values(old_cfg=old_cfg, new_cfg=new_cfg)
    assert return_val["new_items"] == {"key4": "val4"}
    assert return_val["changed_items"] == {"key1": "val1 -> new_val_1", "key3": "val3 -> new_val_3"}


def test_contract_cannot_become_trial():
    old_cfg = {"SalesPhase": "contract", "key2": "val2", "key3": "val3"}
    new_cfg = {"SalesPhase": "trial", "key3": "new_val_3", "key4": "val4"}
    with pytest.raises(InvalidSalesPhaseChange):
        CfnParamUpdate.gen_changed_values(old_cfg=old_cfg, new_cfg=new_cfg)


@pytest.mark.manual_test
def test_manual():
    perform_changes_params = copy.deepcopy(params)
    perform_changes_params.show_changes_only = False
    print(main(asdict(perform_changes_params)))
