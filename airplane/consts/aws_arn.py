def get_arn(service: str, account_id: str, resource_name: str, region: str = ""):
    return f"arn:aws:{service}:{region}:{account_id}:{resource_name}"
