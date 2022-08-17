# Sentry to Asana Integration Service

This service handles Sentry events and creates Asana tasks for each event, thus replacing
the manual process of the on-call engineer triaging such events.

## Architecture

The service follows a single producer, single consumer pattern. However, we actually achieve multiple producer, multiple consumer (MPMC)
because of how AWS Lambda scales up for both lambas and how AWS determines when to send messages (in batches) to the consumer.

The producer's job is to capture Sentry events, format an SQS message and place on an SQS queue. The consumer's job is to process those messages on the queue in a reliable way. It is driven by SQS events and will process multiple messages on the queue.

#### Failure Impacts:

Producer

- Loss of the Sentry event. Manually look at CloudWatch logs and re-create/send the payload or create the task manually in Asana.

Consumer

- Sentry event is retried up to 10x only for failed records in the batch of events
- Continuously failed events land in a DLQ for manual requeuing

## Updating Entity Ownership Mapping

All entity ownership definitions live in `./sentry_asana/src/common/components/entities/data/teams.yaml`

These definitions define what teams are responsible for which entities.

An example entry in teams.yaml is as follows:

```
  # Your team name.
  name: "Investigations"
  
  # The ID of your teams Backlog project in Asana. Low priority tickets are routed here. 
  AsanaBacklogId: '1200908948600028'
  
  # The ID of your teams Sprint portfolio in Asana. High priority tickets are routed here.
  AsanaSprintPortfolioId: '1201675315244000'
  
  # The ID of your teams Sandbox portfolio in Asana. Issues from local development deployments are routed here.
  AsanaSandboxPortfolioId: '1201700591175689'
  
  # The ID of your Asana Team.
  AsanaTeamId: '1199906290951706'
  
  # The list of Matchers that identify the entities your team is responsible for.
  Entities: [
    
    # Match on Lambda Function name with server_name:<function name>
    Matchers: ["server_name:panther-alerts-api"],

    # Match on URL Paths with url:<url_path> for Frontend Issues.
    Matchers: ["url://investigate//"],

    # Match on a tag using a regular expression. This will apply re.search(pattern, text) to the tag value.
    Matchers: ["server_name:/\\.compute\\.internal/"],
    Matchers: ["server_name:/\\.ec2\\.internal/"],
    Matchers: ["server_name:/Panther-EFS/"],
    
    # Custom tags other than just server_name and url are supported.
    Matchers: ["alert_owner:investigations"],
    
    # Each matcher is a list and supports statements AND'd together. 
    # In this case we match when the server_name is any EC2 resource and alert_owner is defined as Investigations.
    Matchers: ["server_name:/\\.ec2\\.internal/", "alert_owner:investigations"],
  ]

```

## Finding and Updating Asana Team IDs

If the team IDs within Asana change, or new teams have been added and the team ID code in `./sentry_asana/src/common/components/entities/data/teams.yaml` needs to be updated, a list of team IDs can be found by executing the following API call:

```
curl -H "Authorization: Bearer ***)" \
  https://app.asana.com/api/1.0/projects/1201030803218059/custom_field_settings | \
  jq '.data | map(select(.custom_field.gid == "1199906290951705"))'
```

## Credentials

The service requires the following secrets:

- Sentry_Asana_Secrets
  - `SENTRY_CLIENT_SECRET`: found in the custom integration setup in Sentry. See https://sentry.io/settings/panther-labs/developer-settings/ to view all custom integrations. `Sentry-Asana-Prod` is the integration that corresponds to the service deployed in the `hosted-ops` account (i.e. 'Prod'). For development, please use the Client Secret in `Sentry-Asana-Dev`.
  - `ASANA_PAT`: the PAT used as the bearer token during Asana API calls. Create a PAT here https://app.asana.com/0/my-apps
  - `SENTRY_PAT`: the PAT used as the bearer token during Sentry API. Create a PAT here https://sentry.io/settings/account/api/auth-tokens/
  - `DATADOG_SECRET_TOKEN`: the $DATADOG_SECRET_TOKEN value we have defined as a custom header in our Datadog webhook. See https://app.datadoghq.com/integrations/webhooks?search=webhook to get this value.
  - `DATADOG_API_KEY`: the Datadog API Key used during Datadog API calls. Create an API key here: https://app.datadoghq.com/organization-settings/api-keys
  - `DATADOG_APP_KEY`: the Datadog App Key used during Datadog API calls. Create an App key here: https://app.datadoghq.com/organization-settings/application-keys

## Setup Association Between Asana and Sentry

In order for comments and breadcrumbs to be posted back into Sentry from Asana we need to setup an association. 
In Production this is done via a service account but in Development you'll need to do this association between your personal Sentry and Asana accounts.

- Login to Asana via Okta
- Login to Sentry via Okta
- While logged in, click this link https://sentry.io/account/settings/social/associate/asana/, which performs the handshake and now the Asana identity will always be the service account for comments (including inside sentry).

## Deploying The Service

### Prod

To deploy in **prod** (i.e. `panther-hosted-ops` account), all you need to do is submit a PR. On merge, it will automatically trigger a [codebuild](https://github.com/panther-labs/hosted-aws-management/blob/master/panther-hosted-ops/us-west-2/sentry-asana-codebuild.yml) job to build and update the infrastrucutre and code for the project.

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
  - Install python 3.9 using pyenv (patch version doesn't matter). It is needed to create the `venv` with a version of python that we want.
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
  - Install all development dependencies in the top-level requirements file
    - `pip install -r requirements.txt`
- Setup Pulumi (skip the remaining bullets if you have your dev env configured)
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

- Ensure that a `Pulumi.dev-<YOUR_STACKNAME>.yaml` Pulumi config file exists in the top level directory. If one does not exist, create the file. The config file should look identical to `Pulumi.sentry-asana.yaml` in its content, with correct values for the following:

Example for `Pulumi.dev-nick-sentry.yaml`:
```
config:
  sentry-asana-integration:deploymentParams:
    # Set to true for local dev
    development: true
    alarmEmailSubscriptions:
      - nick.angelou@panther.io
```
Definitions:
  - `deploymentParams`
    - `development`: An indicator to run in dev mode which uses dev asana boards. Ensure this is set to `true`!
    - `alarmActionsTopic`: **Not needed for local dev**, but this is a list of unmanaged topic arns inside hosted-ops where unmanaged means it is set up outside of this repository. Currently, there is only one topic (`hosted-ops-on-call`) to notify on-call (PagerDuty) when unhandled exceptions happen in Lambda or if there are messages that land in the DLQ.
    - `alarmEmailSubscriptions`: This is a list of email addresses that will be added as subscriptions to an SNS topic that is managed by this project. Very useful for debugging and in production this is the observability's gmail group.
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

