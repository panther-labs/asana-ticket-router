## Deploying Instructions ##
- Run the following : `dev -- aws cloudformation deploy --template-file sentry_asana_integration/cloudformation/codebuild.yaml --stack-name yusuf-dev-sentry-asana-pulumi-stack --region us-west-2 --capabilities CAPABILITY_NAMED_IAM`
- If using S3 as the source, use the following syntax:
    ```
          Source:
        BuildSpec: |
          version: 0.2
          phases:
            install:
              commands:
                - python3 -m venv venv
                - venv/bin/pip3 install pulumi pulumi-aws
            pre_build:
              commands:
                - pulumi version
                - pulumi whoami
                - pulumi stack init --stack $STACK_NAME || echo "stack already exists"
            build:
              commands:
                - pulumi up --skip-preview --yes --stack $STACK_NAME --config-file Pulumi.dev-yakhtar-sentry-asana.yaml
        Location: sentry-asana-test-deployment-bucket/
        Type: S3
      TimeoutInMinutes: 30
    ```
    - The command to sync the source in the bucket: `dev -- aws s3 cp ./sentry_asana_integration s3://sentry-asana-test-deployment-bucket/sentry_asana_integration/ --recursive`
    - Also add the following permissions:
    ```
                - Effect: Allow
                Action: s3:*
                Resource:
                  - arn:aws:s3:::sentry-asana-test-deployment-bucket
                  - arn:aws:s3:::sentry-asana-test-deployment-bucket/*
    ```