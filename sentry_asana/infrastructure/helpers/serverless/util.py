# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
import os
import subprocess  # nosec: True
import shutil
from sentry_asana.infrastructure.globals import PROJECT_ROOT, \
    SRC_FOLDER_NAME, LAMBDA_DEPLOYMENT_PACKAGE_DIR, INIT_PATH, COMMON_PATH


def create_lambda_package(src_path: str) -> str:
    """Helper to package a lambda specified by the path to its source"""
    lambda_path = os.path.join(PROJECT_ROOT, SRC_FOLDER_NAME, src_path)
    common_path = os.path.join(PROJECT_ROOT, SRC_FOLDER_NAME, COMMON_PATH)
    init_path = os.path.join(PROJECT_ROOT, SRC_FOLDER_NAME, INIT_PATH)
    package_path = os.path.join(
        LAMBDA_DEPLOYMENT_PACKAGE_DIR, src_path)
    shutil.rmtree(package_path, ignore_errors=True)
    os.makedirs(package_path)

    # Copy all src files into new dir; shutil.copytree, the most suggested way of doing this
    # in python, apparently has some issues that cause unexpected headaches
    subprocess.call(  # nosec: True
        ['cp', '-r', lambda_path, package_path], shell=False
    )

    subprocess.call(  # nosec: True
        ['cp', '-r', common_path, package_path], shell=False
    )

    # Copy over __init__.py file
    subprocess.call(  # nosec: True
        ['cp', '-r', init_path, package_path], shell=False
    )
    # Install the wheels for linux + arm64 for Graviton2.
    # NOTE: this is not compatible with x86.
    subprocess.call(  # nosec: True
        [
            'pip',
            'install',
            '--platform=manylinux2014_aarch64',
            '--only-binary=:all:',
            '-q',
            '-r',
            os.path.join(lambda_path, 'requirements.txt'),
            '-t',
            package_path
        ],
        shell=False
    )
    return package_path
