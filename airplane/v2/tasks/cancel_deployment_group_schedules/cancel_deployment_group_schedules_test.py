from v2.tasks.cancel_deployment_group_schedules.cancel_deployment_group_schedules import CancelDeploymentGroupSchedules

if __name__ == '__main__':
    params = {
        "all_groups": False,
        "group_a": True,
        "group_c": True,
        "group_j": False,
        "group_n": True,
        "hosted_deployments_path": ""
    }
    CancelDeploymentGroupSchedules(is_dry_run=True).run(params)
