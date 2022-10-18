import os

DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
REGION = os.environ.get('AWS_REGION')

# Lambda parameters
LAMBDA_TIMEOUT_SECONDS = 120
LAMBDA_RUNTIME_VERSION = '3.9'
LAMBDA_RUNTIME = f'python{LAMBDA_RUNTIME_VERSION}'
LAMBDA_ARCHITECTURE = 'arm64'
LAMBDA_FILE = 'handler'
LAMBDA_HANDLER = 'handler'
SQS_VISIBILITY_TIMEOUT_SECONDS = LAMBDA_TIMEOUT_SECONDS
IS_DEBUG = 'true' if DEBUG is True else 'false'

# SQS event mapping
BATCH_SECONDS = 5

# Packaging
LAMBDA_DEPLOYMENT_PACKAGE_DIR = '.deployments'
PROJECT_NAME = 'sentry-asana'
PROJECT_ROOT = 'sentry_asana'
SRC_FOLDER_NAME = 'src'
INIT_PATH = '__init__.py'
COMMON_PATH = 'common'
LAMBDA_CONSUMER = 'consumer'
LAMBDA_PRODUCER = 'producer'

# Datadog lambda extension
DATADOG_LAMBDA_EXTENSION_VERSION = 29
DATADOG_PYTHON_LAYER_VERSION = 62
