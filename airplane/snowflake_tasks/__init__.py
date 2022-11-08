import airplane

from pyshared.aws_consts import get_aws_const

ENV_VARS = [airplane.EnvVar(name="ECS_TASK_ROLE", value=get_aws_const("SNOWFLAKE_READ_MASTER_CREDENTIALS"))]
