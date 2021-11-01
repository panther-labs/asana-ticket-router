# Sentry to Asana Integration Service

This service handles Sentry events and creates Asana tasks for each event, thus replacing
the manual process of the on-call engineer triaging such events.

## Deploying The Service ##
In order to deploy the service manually (i.e. not through CI/CD), Pulumi CLI is required (see https://www.pulumi.com/docs/reference/cli/ for install details). Complete your Pulumi setup (including access token related work) prior to deploying.

#### Dev ####
To deploy in **dev**, the steps are as follows:
- Ensure that a `Pulumi.dev-<YOUR_STACKNAME>.yaml` Pulumi config file exists. If one does not exist, create the file and ensure it is gitignored by the existing entry in the `.gitignore`. The config file should look identical to `Pulumi.sentry-asana.yaml` in its content, with correct values for the following:
    - `deploymentParams`
        - `metricAlarmActionsArns`: A list of SNS topics to which the Cloudwatch alarm(s) that will be created will use as their alarm actions.
        - `snsTopicSubscriptionEmailAddresses`: A list of email addresses that will be added as subscriptions to the default SNS topic that gets created.
- Run the following command, replacing the <> brackets as needed: `AWS_REGION=us-west-2 dev -- pulumi up --config-file Pulumi.dev-<YOUR_STACK_NAME>.yaml --stack panther-dev/<YOUR_STACK_NAME>`
    - The command should prompt you to confirm creation of the stack if the stack does not exist

#### Prod ####
To deploy in **prod** (i.e. panther-hosted-ops account), trigger the codebuild project through the console to deploy what is on `Main`.


### Updating the Team IDs

```
curl -H "Authorization: Bearer ***)" \
  https://app.asana.com/api/1.0/projects/1201030803218059/custom_field_settings | \
  jq '.data | map(select(.custom_field.gid == "1199906290951705"))' 
```
