from operations.cfn_param_update.cfn_param_update import main as common_main


def main(params):
    params["requires_parent_execution"] = True
    return common_main(params)
