import pytest

from dataclasses import asdict

from operations.upgrade_deployment_groups.upgrade_deployment_groups import AirplaneParams, main
from v2.exceptions import ConflictingParameterException


@pytest.mark.manual_test
def test_specific_groups():
    # In order to test all groups, you can change the deployment_groups parameter to be all_groups=True
    # Be sure to undo git changes between the tests of deployment_groups vs all_groups
    params = AirplaneParams(deployment_groups="a,c,z", version="9.9.9")
    main(asdict(params))

@pytest.mark.manual_test
def test_fail_if_both_parameters_are_used():
    # In order to test all groups, you can change the deployment_groups parameter to be all_groups=True
    # Be sure to undo git changes between the tests of deployment_groups vs all_groups
    params = AirplaneParams(deployment_groups="a,c,z", all_groups=True, version="9.9.9")
    with pytest.raises(ConflictingParameterException):
        main(asdict(params))
