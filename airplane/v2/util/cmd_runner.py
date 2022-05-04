import subprocess

from v2.pyshared.os_util import join_paths, get_current_directory


def run_cmd(script_name: str, cmd: str = "") -> str:
    try:
        script_abs_path = join_paths(get_current_directory(__file__), script_name)
        return subprocess.check_output(f"{cmd} {script_abs_path}", shell=True, stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command '{e.cmd}' returned with error (code {e.returncode}): {e.output.decode()}")
