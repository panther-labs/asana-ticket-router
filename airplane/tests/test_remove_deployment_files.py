from dataclasses import asdict

import pytest

from operations.deprovisions.remove_deployment_files.remove_deployment_files import main, AirplaneParams

ap_params = AirplaneParams(fairytale_name="electric-ladybug", organization="hosted")
params = asdict(ap_params)


@pytest.mark.manual_test
def test_manual():
    print("Be sure to check that the expected files are removed and that Makefile and account-mapping.yml are modified!")
    main(params)
