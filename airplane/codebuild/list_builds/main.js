import { STSClient, AssumeRoleCommand } from "@aws-sdk/client-sts";
import { CodeBuildClient, ListBuildsForProjectCommand, BatchGetBuildsCommand } from "@aws-sdk/client-codebuild";

export default async function (params) {
  const account = params.aws_account_id
  const region = params.region
  const project = params.project_name
  const count = params.count

  // STS
  const credentials = assumeRole(account, region)

  // List Builds
  console.log("Listing builds")
  const client = new CodeBuildClient({ region: region, credentials: credentials })
  const listResponse = await client.send(new ListBuildsForProjectCommand({
    projectName: project,
  }));

  const ids = listResponse.ids.slice(0, count)
  const getQuery = {
    ids: ids,
  };

  const response = await client.send(new BatchGetBuildsCommand(getQuery));

  const builds = []
  for (const build of response.builds) {
    builds.push({
      'id': build.id,
      'arn': build.arn,
      'complete': build.buildComplete,
      'number': build.buildNumber,
      'status': build.buildStatus,
      'startTime': `${build.startTime}`,
      'endTime': `${build.endTime}`,
    })
  }

  const data = {
    'builds': builds
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
