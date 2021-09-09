# Sentry to Asana Integration Service

This service handles Sentry events and creates Asana tasks for each event, thus replacing
the manual process of the on-call engineer triaging such events.

## Deploying The Service ##
In order to deploy the service manually (i.e. not through CI/CD), Pulumi CLI is required (see https://www.pulumi.com/docs/reference/cli/ for install details). Complete your Pulumi setup (including access token related work) prior to deploying.

To deploy in *dev*, the steps are as follows:
- Ensure that a `Pulumi.dev-<YOUR_STACKNAME>.yaml` file exists. If one does not exist, create the file and add it to the gitignore. The file should look identical to `Pulumi.sentry-asana.yaml` in its content, with correct values for the following:
    - SNS topic (create an SNS topic in your target deployment account and copy that ARN in the config file)
- Run the following command, replacing the <> brackets as needed: `AWS_REGION=us-west-2 dev -- pulumi up --config-file Pulumi.dev-<YOUR_STACK_NAME>.yaml --stack panther-dev/<YOUR_STACK_NAME>`
    - The command should prompt you to confirm creation of the stack if the stack does not exist

To deploy in *prod* (i.e. panther-hosted-ops account), trigger the codebuild project through the console to deploy what is on `Main`.
