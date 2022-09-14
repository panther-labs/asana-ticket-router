import { STSClient, AssumeRoleCommand } from "@aws-sdk/client-sts";
import { CodeBuildClient, ListProjectsCommand } from "@aws-sdk/client-codebuild";

export default async function (params) {
  const account = params.aws_account_id

  // STS
  const credentials = assumeRole(account)


  console.log("Listing projects")
  // List Projects
  const regions = ["us-west-2", "us-east-1", "us-east-2"]
  const projects = []
  for (const region of regions) {
    console.log(`For region ${region}`)
    const client = new CodeBuildClient({ region: region, credentials: credentials })
    const command = new ListProjectsCommand({});
    const response = await client.send(command);
    for (const project of response.projects) {
      console.log(` - ${project}`)
      projects.push({
        'id': project,
        'region': region,
      })
    }
  }

  const data = {
    'projects': projects
  }

  return data
}


async function assumeRole(account) {
  const client = new STSClient({ region: "us-west-2" });
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
    console.log('caught sts error', error)
    throw(error)
  }
}
