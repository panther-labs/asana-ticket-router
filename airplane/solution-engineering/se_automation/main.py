# Linked to https://app.airplane.dev/t/se_automation [do not edit this line]

import os, notional
from notional import types
from notional.orm import Property, connected_page

from pyshared.aws_secrets import get_secret_value


def main(params):
    if params['task'] == 'customer-notes':
        custNotes()


'''
Prereqs: notional

Purpose: Scan the Customer Notes database in Notion for known values, add them where needed

Process:
You need a Notion API key for this script (not provided, get it from someone)
You need to Share the database itself with the Notion Integration correlated with your API key
You can extract the Database ID from the URL of the TABLE (NOT the Page that contains it)
The custom class SEnote is an extension of Notional that allows for I/O to Notion
'''


def custNotes():

    database_id = "089bbc04c4ed4297b5b72e5fecf8c860"

    notion = notional.connect(auth=get_secret_value("airplane/notion-auth-token"))
    CustomPage = connected_page(session=notion)

    # Custom SE Note class
    class SEnote(CustomPage, database=database_id):
        Title = Property("Title", types.Title)
        CustomerIndex = Property("Customer Index", types.Relation)
        Date = Property("Date", types.Date)
        PAttendees = Property("Panther Attendee(s)", types.People)
        CAttendees = Property("Customer Attendee(s)", types.Relation)
        Type = Property("Type", types.MultiSelect)
        Notes = Property("Notes", types.RichText)
        FollowUps = Property("Follow ups", types.RichText)
        Stage = Property("Stage", types.SelectOne)
        Features = Property("Features / Releases", types.MultiSelect)
        Issues = Property("Issues / Gaps", types.MultiSelect)
        DataSources = Property("Data Sources", types.MultiSelect)
        AlertDestinations = Property("Alert Destinations", types.MultiSelect)
        Competitors = Property("Competitors", types.MultiSelect)
        Mood = Property("Customer Mood", types.SelectOne)

    competitors = [
        'Chaos', 'Chronicle', 'Datadog', 'Demisto', 'Devo', 'Elastalert', 'Elastic', 'ELK', 'IBM', 'Loki', 'Obsidian',
        'Phantom', 'Prisma', 'Splunk', 'Sumo'
    ]
    destinations = [
        'Cydarm', 'Halp', 'PagerDuty', 'ServiceNow', 'Slack', 'SOAR', 'Socless', 'TheHive', 'Tines', 'Trello', 'Webhook'
    ]
    features = [
        'Alert', 'API', 'Athena', 'BI', 'CICD', 'CloudFormation', 'Detection', 'DynamoDB', 'Enrichment', 'Indicator',
        'Ingest', 'Integrations', 'JSON', 'MITRE', 'Monitoring', 'Normalization', 'Packs', 'PantherAnalysistool', 'PAT',
        'Python', 'Query', 'RBAC', 'Roadmap', 'SaaS', 'Scheduled', 'Schema', 'Snowflake', 'Snowsight', 'SQL',
        'Terraform', 'UI'
    ]
    sources = [
        'ALB', 'AlienVault', 'Apache', 'Auditd', 'Aviatrix', 'AWS', 'Azure', 'Beacon', 'Box', 'Capsule8', 'Carbon',
        'Cisco', 'CloudFlare', 'CloudFunnel', 'CloudTrail', 'CloudWatch', 'Code42', 'Cortex', 'Cribl', 'CrowdStrike',
        'CSV', 'Custom', 'Cyberhaven', 'Defender', 'Docker', 'Dropbox', 'Duo', 'EC2', 'ECS', 'EDR', 'Egnyte', 'Egress',
        'EKS', 'Exabeam', 'Falco', 'Falcon', 'Fastly', 'Fastmatch', 'FDR', 'Firehose', 'Firewalls', 'Fluentd', 'GCP',
        'Git', 'GitHub', 'Gitlab', 'Greynoise', 'Gsuite', 'GuardDuty', 'Hive', 'IAM', 'IDS', 'Jenkins', 'JIRA', 'Kafka',
        'Kasada', 'Kinesis', 'Kubernetes', 'Lacework', 'LastLine', 'LDAP', 'Linux', 'Mac', 'Meraki', 'MFA', 'Mimecast',
        'MySQL', 'NAS', 'Netskope', 'Nginx', '365', 'Okta', 'OneLogin', 'OpsGenie', 'Osquery', 'Pager Duty', 'Palo',
        'Proofpoint', 'Pulumi', 'RDS', 'S3', 'Safenet', 'Salesforce', 'SAML', 'Sentinel', 'SentinelOne', 'Sigma',
        'Signal Sciences', 'SNS', 'Sophos', 'Spinnaker', 'SQS', 'Syslog', 'Teleport', 'Umbrella', 'VPC', 'VPN', 'WAF',
        'Windows', 'Workday', 'Yes', 'Zendesk', 'Zoom'
    ]

    # Query Notion using our custom class defined above
    # Notional allows for I/O using custom classes
    query = notion.databases.query(SEnote)

    for note in query.execute():
        for c in competitors:
            if c in note.Notes or c in note.FollowUps:
                try:
                    note.Competitors += c
                except:
                    print('error')

        for d in destinations:
            if d in note.Notes or d in note.FollowUps:
                try:
                    note.AlertDestinations += d
                except:
                    print('error')

        for f in features:
            if f in note.Notes or f in note.FollowUps:
                try:
                    note.Features += f
                except:
                    print('error')

        for s in sources:
            if s in note.Notes or s in note.FollowUps:
                try:
                    note.DataSources += s
                except:
                    print('error')

        try:
            note.commit()
        except:
            print('error')
