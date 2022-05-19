import pytest

from notion.update_deployment_records.update_panther_deployments_notion_records import UpdateDeploymentRecords, main


@pytest.mark.manual_test
def test_manual():
    print(f"{UpdateDeploymentRecords.WARNING_COLOR}This is a test run, so no Notion entries will be updated")
    UpdateDeploymentRecords.add_test_role("hosted", "hosted-root-read-only", "us-west-2")
    UpdateDeploymentRecords.add_test_role("staging", "root-read-only", "us-west-2")
    UpdateDeploymentRecords.set_env_var_from_onepass_item(env_var_name="NOTION_AUTH_TOKEN",
                                                          onepass_item_name="Notion - Productivity")
    main({})
