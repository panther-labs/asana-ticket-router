# Sentry to Asana Integration Service

This service handles Sentry events and creates Asana tasks for each event, thus replacing
the manual process of the on-call engineer triaging such events.

## Architecture

The service follows a single producer, single consumer pattern. However, we actually achieve multiple producer, multiple consumer (MPMC)
because of how AWS Lambda scales up for both lambas and how AWS determines when to send messates (in batches) to the consumer.

The producer's job is to capture Sentry events, format an SQS message and place on an SQS queue. The consumer's job is to process those messages on the queue in a reliable way. It is driven by SQS events and will process multiple messages on the queue.

#### Failure Impacts:

Producer

- Loss of the Sentry event. Manually look at CloudWatch logs and re-create/send the payload or create the task manually in Asana.

Consumer

- Sentry event is retried up to 10x only for failed records in the batch of events
- Continuously failed events land in a DLQ for manual requeuing

## Credentials

The service requires the following secrets:

- Sentry_Asana_Secrets
  - SENTRY_CLIENT_SECRET: found in the custom integration setup in Sentry. See https://sentry.io/settings/panther-labs/developer-settings/ to view all custom integrations. `Sentry-to-Asana-Hosted-Ops` is the integration that corresponds to the service deployed in the `hosted-ops` account (i.e. 'Prod'). For development, use the Client Secret in `Sentry-to-Asana-Dev`.
  - ASANA_PAT: the PAT used as the bearer token during Asana API calls. Create a PAT here https://app.asana.com/0/my-apps
  - SENTRY_PAT: the PAT used as the bearer token during Sentry API. Create a PAT here https://sentry.io/settings/account/api/auth-tokens/

## Deploying The Service

### Prod

To deploy in **prod** (i.e. panther-hosted-ops account), trigger the codebuild project through the console to deploy what is on the `main` branch.
In order to deploy the service manually (i.e. through the Pulumi CLI), Pulumi CLI is required (see https://www.pulumi.com/docs/reference/cli/ for install details). Complete your Pulumi setup (including access token related work) prior to deploying.

### Dev

### Create an AWS Secret

You must create an AWS Secret containing the 3 credentials in the above section in your dev account

- Navigate to AWS Secrets Manager
- Ensure you're in the appropriate region
- Click on `Store a new secret`
- Select `Other type of secret` which will give you a key/value input
- Enter the three keys (case-sensitive) and corresponding values
- Name the secret `Sentry_Asana_Secrets` and create

### Set up your dev environment

- Setup python environment
  - Install python 3.9 using pyenv. It is needed to create the `venv` with a version of python that we want.
    - `brew install pyenv`
    - `pyenv install 3.9.9`
    - `pyenv local 3.9.9`
  - Install venv next to contain packages. In the future we wont need this, but it is legacy.
    - Verify that you're on python 3.9.9
    - `python --version` should show `Python 3.9.9`
    - Then create the venv directory
    - `python -m venv venv`
    - Activate the venv. This will show `(venv)` prefixed to your terminal.
    - `source venv/bin/activate`
  - Install deps
    - `pip install -r requirements.txt`
- Setup Pulumi
  - Install Pulumi
    - `brew install pulumi`
    - See https://www.pulumi.com/docs/reference/cli/ for instructions
  - Login through the Pulumi CLI
    - `pulumi login`
    - See https://www.pulumi.com/docs/reference/cli/pulumi_login/ for instructions
- Ensure AWS Access
  - Ensure you have aws-vault setup and can execute AWS CLI commands against your dev account
    - See https://www.notion.so/pantherlabs/Onboarding-ba183bf1483746d2acb027c21c5a17a5 for detailed instructions
  - Setup an alias for your aws-vault role assumption command
    - `alias dev="aws-vault exec dev-your-admin"`

### Deploy to your dev account

- Ensure that a `Pulumi.dev-<YOUR_STACKNAME>.yaml` Pulumi config file exists in the top level directory. If one does not exist, create the file and ensure it is gitignored by the existing entry in the `.gitignore`. The config file should look identical to `Pulumi.sentry-asana.yaml` in its content, with correct values for the following:
  - `deploymentParams`
    - `development`: An indicator to run in dev mode which uses dev asana boards.
    - `alarmActionsTopic`: This is a list of unmanaged topic arns inside hosted-ops. Currently, there is only one (`hosted-ops-on-call`) to notify on-call (PagerDuty) when exceptions happen in Lambda or if there are messages in the DLQ.
    - `alarmEmailSubscriptions`: This is a list of email addresses that will be added as subscriptions to an SNS topic that is managed by this project. It also notifies on exceptions in Lambda or if there are messages in the DLQ. We provide a controlled SNS topic for development and also to act as an additional notification layer.
- Run the following command, replacing the <> brackets as needed: `AWS_REGION=us-west-2 dev -- pulumi up --config-file Pulumi.dev-<YOUR_STACK_NAME>.yaml --stack panther-dev/dev-<YOUR_STACK_NAME>`
  - The command should prompt you to confirm creation of the stack if the stack does not exist

## Linting & Unit Tests

It is advisable to run the unit tests and lint commands periodically and prior to opening a PR, as they are required checks in CircleCI. As a convenience, the commands to run the unit tests and lint have each been added to scripts named `python_unit_test.sh` and `python_lint.sh` respectively. These scripts contain the exact commands run by CircleCI.

To run them, do the following:

- Setup your virtual environment and install top level dependencies (requirements.txt at the directory root)
- Run the linting script
  - `sh scripts/python_lint.sh`
- Run the unit testing script
  - `sh scripts/python_unit_test.sh`

## Updating the Team IDs

If the team IDs within Asana change, or new teams have been added and the team ID code in `src/enum/teams.py` needs to be updated, a list of team IDs can be found by executing the following API call:

```
curl -H "Authorization: Bearer ***)" \
  https://app.asana.com/api/1.0/projects/1201030803218059/custom_field_settings | \
  jq '.data | map(select(.custom_field.gid == "1199906290951705"))'
```
