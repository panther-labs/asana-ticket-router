# New Customer Deployments

## Usage
Find the new-customer-deployments runbook in Airplane and execute it.

## How It Works
* The script in the new-customer-deployments directory sets up git
* Then it calls Python scripts from the hosted deployments repo (which is cloned to the runner's environment)
* New files generated from those scripts are committed
* The commit action triggers a Github Action that deploys a new customer account

