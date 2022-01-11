# Requires 1Password CLI to be installed
while ! op list vaults &> /dev/null ; do
  echo "*** Signin to OnePassword ***"
  eval "$(op signin)"
done

# Requires Python virtual environment to be setup at ~/.venvs/airplane
VENV_AP=~/.venvs/airplane
PY=${VENV_AP}/bin/python
PIP=${VENV_AP}/bin/pip

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
SCRIPT="${SCRIPT_PATH}/update_deployment_records.py"
AP_PATH="${SCRIPT_PATH}/../.."

# May need to update this to match your environment
HOSTED_DEPLOY_DIR="${SCRIPT_PATH}/../../../../hosted-deployments"

export NOTION_AUTH_TOKEN=$(op get item 'Notion - Productivity' --fields credential)
export PATH="${PATH}:${AP_PATH}"
export PYTHONPATH="${PYTHONPATH}:${AP_PATH}"

aws-vault exec hosted-root-airplane-dynamodb-read-only -- "${PY}" << EOF
import importlib.util

spec = importlib.util.spec_from_file_location("module.name", "${SCRIPT}")
py_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(py_module)
params = {"hosted_deploy_dir": "${HOSTED_DEPLOY_DIR}"}
print(f"Output of Airplane task: {py_module.main(params)}")
EOF