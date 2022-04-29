import subprocess


def get_item(item_name, field_name="credential"):
    return subprocess.check_output(f"op item get '{item_name}' --fields '{field_name}'",
                                   shell=True).decode().rstrip("\n")
