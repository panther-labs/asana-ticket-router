from operations.cfn_param_update.cfn_param_update import main as common_main


def main(params):
    params["show_changes_only"] = True
    return common_main(params)
