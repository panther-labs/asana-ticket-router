# Note: unit testing this task is quite difficult, as most of the logic takes place in hosted-deployments. Instead,
# this ensures the interface is used properly.
import pytest
from unittest import mock

from operations.deployment.new_customer import create_new_customer
from operations.deployment.new_customer.create_new_customer import main

# Only template URL is needed for testing
generated_customer_file = {
    "PantherTemplateURL": "https://panther-enterprise-us-east-1.s3.amazonaws.com/v1.35.4/panther.yml"
}


def get_params():
    return {
        "account_name": "Create Customer Test",
        "region": "us-west-2",
        "backend": "Managed",
        "deploy_group": "L",
        "first_name": "Tim",
        "last_name": "Scott",
        "email_address": "tim.scott@panther.io",
    }


@pytest.fixture(scope="function", autouse=True)
def setup_mocks(manual_test_run, request):
    if not manual_test_run:
        for func_name, rval in {
                "AirplaneGitTask.clone_repo_or_get_local": None,
                "AirplaneGitTask.git_add_commit_and_push": None,
                "generate_fairytale_name": "alpha-doe",
                "load_yaml_cfg": generated_customer_file,
                "pip_install_auto_scripts_requirements": None,
                "tmp_change_dir": None,
        }.items():
            patch_obj = mock.patch(f"{create_new_customer.__name__}.{func_name}")
            mock_obj = patch_obj.start()
            if rval is not None:
                mock_obj.return_value = rval
            request.addfinalizer(patch_obj.stop)


@pytest.fixture(scope="function", autouse=True)
def create_customer_metadata(manual_test_run):
    if manual_test_run:
        yield None
    else:
        with mock.patch(f"{create_new_customer.__name__}.create_customer_file") as create_customer_file:
            create_customer_file.return_value = "alpha-doe"
            yield create_customer_file


def _get_cfg_args(metadata_mock):
    return metadata_mock.call_args[1]["customer_cfg"]


def test_translated_args_passed_properly_to_create_customer_metadata(create_customer_metadata):
    main(get_params())
    cfg = _get_cfg_args(create_customer_metadata)
    assert cfg["customer_id"] == "alpha-doe"
    assert cfg["customer_display_name"] == "Create Customer Test"
    assert cfg["region"] == "us-west-2"
    assert cfg["snowflake_deployment"] == "Managed"
    assert cfg["group"] == "l"
    assert cfg["contact_first_name"] == "Tim"
    assert cfg["contact_last_name"] == "Scott"
    assert cfg["contact_email"] == "tim.scott@panther.io"
    assert "customer_domain" not in cfg


def test_domain_given(create_customer_metadata):
    params = get_params()
    params["customer_domain"] = "my-cool-domain"
    main(params)
    cfg = _get_cfg_args(create_customer_metadata)
    assert cfg["customer_domain"] == "my-cool-domain"


def test_outputs():
    output = main(get_params())
    assert output["fairytale_name"] == "alpha-doe"
    assert output["panther_version"] == "v1.35.4"


@pytest.mark.manual_test
def test_manual():
    main(get_params())
