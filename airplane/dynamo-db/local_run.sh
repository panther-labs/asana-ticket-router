#!/bin/sh -eu

FAIRYTALE_NAME="tulgey-wood"
SCRIPT="${1}"

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
VENV_BASE_DIR=~/.venvs
VENV_AP=${VENV_BASE_DIR}/airplane-dynamodb
PY=${VENV_AP}/bin/python
PIP=${VENV_AP}/bin/pip

if [ ! -d ${VENV_AP} ]; then
  mkdir -p ~/.venvs
  python3 -m venv ${VENV_AP}
  ${PIP} install -r "${SCRIPT_PATH}/requirements.txt"
fi

aws-vault exec hosted-root-airplane-dynamodb-read-only -- "${PY}" << EOF
import importlib.util
spec = importlib.util.spec_from_file_location("module.name", "${SCRIPT}")
py_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(py_module)
print(py_module.main({"fairytale_name": "${FAIRYTALE_NAME}"}))
EOF
