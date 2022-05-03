import subprocess


def run_cmd(cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command '{e.cmd}' returned with error (code {e.returncode}): {e.output.decode()}")
