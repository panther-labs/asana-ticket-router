#!/bin/bash
# Linked to https://app.airplane.dev/t/shell_test_env [do not edit this line]
# Script for testing other shell tasks. Feel free to overwrite and use this for your testing purposes!
set -eu
source util/task-dir
cd_to_task_dir

FAIRYTALE_NAME="testing123"
echo "A line before"
echo "airplane_output_set {\"fairytale_name\": \"${FAIRYTALE_NAME}\"}"
# Just to have something in-between the echo airplane output and further echo statements
sleep 5
echo "Another line after"
