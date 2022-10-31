def main(params):
    fairytale_name = params.get("connected_fairytale_name")
    if fairytale_name and params["backend"] != "Connected":
        raise ValueError("Cannot set fairytale name unless this is a Connected backend")
    # TODO: Verify Connected secret actually exists in AWS hosted-root secrets for fairytale name
