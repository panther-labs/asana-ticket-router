from v2.tasks.update_deployment_group_schedules.update_deployment_group_schedules import UpdateDeploymentGroupSchedules

if __name__ == '__main__':
    params = {
        "deployment_version": "v1.34.11",
        "group_a_deployment_date": "2022-05-05",
        "group_n_deployment_date": "2022-05-05",
        "group_a_deployment_time": "10:00 AM",
        "group_n_deployment_time": "10:00 AM",
        "group_c_deployment_date": "2022-05-05",
        "group_c_deployment_time": "10:00 AM",
        "hosted_deployments_path": ""
    }
    UpdateDeploymentGroupSchedules(is_dry_run=True).run(params)
