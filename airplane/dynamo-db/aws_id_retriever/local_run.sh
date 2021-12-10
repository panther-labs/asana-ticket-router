#!/bin/sh -eu

FAIRYTALE_NAME="tulgey-wood"
SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
SCRIPT=${SCRIPT_PATH}/aws_id_retriever.py
VENV_BASE_DIR=~/.venvs
VENV_AP=${VENV_BASE_DIR}/airplane-dynamodb
PY=${VENV_AP}/bin/python
PIP=${VENV_AP}/bin/pip

if [ ! -d ${VENV_AP} ]; then
  mkdir -p ~/.venvs
  python3 -m venv ${VENV_AP}
  ${PIP} install -r "${SCRIPT_PATH}/../requirements.txt"
fi

aws-vault exec hosted-root-airplane-dynamodb-read-only -- "${PY}" "${SCRIPT}" "${FAIRYTALE_NAME}"
