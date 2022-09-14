import { STSClient, AssumeRoleCommand } from "@aws-sdk/client-sts";
import { CodeBuildClient, BatchGetBuildsCommand } from "@aws-sdk/client-codebuild";
import { CloudWatchLogsClient, GetLogEventsCommand } from "@aws-sdk/client-cloudwatch-logs";

export default async function (params) {
  const account = params.aws_account_id
  const region = params.region
  const project = params.project_name
  const buildId = params.build

  // STS
  const credentials = assumeRole(account, region)
  const client = new CloudWatchLogsClient({ region: region, credentials: credentials  })
  const codebuildClient = new CodeBuildClient({ region: region, credentials: credentials })

  console.log("Loading build info")
  const codebuildResponse = await codebuildClient.send(new BatchGetBuildsCommand({
    ids: [buildId]
  }));
  const build = codebuildResponse.builds[0]
  console.log(build)

  const options = {
    'logGroupName': build.logs.groupName,
    'logStreamName': build.logs.streamName,
    'limit': 1000,
  }

  console.log("Loading log events")
  //for await (const page of paginateGetLogEvents({ client, pageSize: 5 }, options)) {
  //  log.push(...page.events);
  //}
  const log = [];
  const response = await client.send(new GetLogEventsCommand(options));
  log.push(...response.events)

  const data = {
    'info': {
      'status': `${build.buildStatus}`,
      'startTime': `${build.startTime}`,
      'endTime': `${build.endTime}`,
    },
    'log': log
  }

  return data
}


async function assumeRole(account, region) {
  const client = new STSClient({ region: region });
  const roleArn = `arn:aws:iam::${account}:role/PantherCodeBuildReadOnly`
  console.log("Assuming role:", roleArn)
  const command = new AssumeRoleCommand({
    RoleArn: roleArn,
    RoleSessionName: "airplane-ephemeral",
  });

  try {
    const data = await client.send(command);
    return {
      accessKeyId: data.Credentials.AccessKeyId,
      secretAccessKey: data.Credentials.SecretAccessKey,
      sessionToken: data.Credentials.SessionToken,
    }
  } catch (error) {
    console.log(error)
    throw(error)
  }
}
