import subprocess


def input_mfa_with_av_exec(aws_profile, region=""):
    region = f"region={region}" if region else ""
    subprocess_cmd = (f"zsh -c 'source ~/.zsh_scripts/av-funcs.zsh && av-exec profile_name={aws_profile} {region} "
                      f"cmd=pwd'")
    subprocess.check_output(subprocess_cmd, shell=True).decode()


def aws_vault_exec(aws_profile, cmd, region=""):
    region = f"--region {region}" if region else ""
    subprocess_cmd = f"aws-vault exec {aws_profile} {region} -- {cmd}"
    return subprocess.check_output(subprocess_cmd, shell=True).decode()


def input_mfa(aws_profile, region=""):
    try:
        input_mfa_with_av_exec(aws_profile=aws_profile, region=region)
    except (subprocess.CalledProcessError, FileNotFoundError):
        aws_vault_exec(aws_profile=aws_profile, cmd="pwd", region=region)
