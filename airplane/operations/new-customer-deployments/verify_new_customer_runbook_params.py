def main(params):
    fairytale_name = params.get("byosf_fairytale_name")
    if fairytale_name and params["backend"] != "BYOSF":
        raise ValueError("Cannot set fairytale name unless this is a BYOSF backend")
    # TODO: Verify BYOSF secret actually exists in AWS hosted-root secrets for fairytale name
