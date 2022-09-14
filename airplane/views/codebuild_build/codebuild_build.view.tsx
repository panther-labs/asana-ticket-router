import { TextInput, Column, Stack, Table, Text, Title, Card, Markdown, Button, useComponentState, useTaskQuery, useTaskMutation } from "@airplane/views";
import queryString from "query-string"
import { useState } from "react"

// Put the main logic of the view here.
// Views documentation: https://docs.airplane.dev/views/getting-started
const CodeBuildView = () => {
  const [submit, setSubmit] = useState(false);

  const buildsState = useComponentState("builds");
  const selectedBuild = buildsState.selectedRow;

  const accountState = useComponentState("account");
  const regionState = useComponentState("region");
  const projectState = useComponentState("project");

  const accountSet = accountState.value !== ''
  const regionSet = regionState.value !== ''
  const projectSet = projectState.value !== ''
  const inputsSet = accountSet && regionSet && projectSet

  const queryParams = queryString.parse(window.location.search)
  if (queryParams.account) {
    accountState.setValue(queryParams.account)
  }
  if (queryParams.region) {
    regionState.setValue(queryParams.region)
  }
  if (queryParams.project) {
    projectState.setValue(queryParams.project)
  }

  function handleSubmit(e) {
    e.preventDefault();
    console.log('You clicked submit.');
    setSubmit(true)
  }

  const detailState = useComponentState("buttons");
  const detailResult = detailState.result
  console.log(detailResult)

  return (
    <Stack>
      <TextInput id="account" label="AWS Account ID" />
      <TextInput id="region" label="Region" />
      <TextInput id="project" label="Project Name" />
      <Button id="submitButton" onClick={handleSubmit} disabled={!inputsSet}>
        Load Builds
      </Button>
      {submit && (<>
        <Title>Builds</Title>
        <Stack>
          <Table
            id="builds"
            title="Builds"
            task={{slug: "list_codebuild_builds", refetchInterval: 60000, params: {
                aws_account_id: accountState.value,
                region: regionState.value,
                project_name: projectState.value,
                count: 3,
              }}}
            rowSelection="single"
            defaultPageSize="3"
            // rowActions={["pet_cat", { slug: "feed_cat", label: "Feed" }]}
          />
          {selectedBuild && (
            <Stack direction="row" grow>
              <BuildDetail account={accountState.value} region={regionState.value} project={projectState.value} build={selectedBuild} />
            </Stack>
          )}
        </Stack>
      </>)}

    </Stack>
  );
};

const BuildDetail = ({ account, region, project, build }) => {

  const params = {
      slug: 'get_codebuild_build',
      aws_account_id: account,
      region: region,
      project_name: project,
      build: build.id
  };

  const { output, loading, error, refetch } = useTaskQuery({
    slug: 'get_codebuild_build',
    params: params,
    executeOnMount: true,
  });

  const userDetail = `### Build: _${build.name}_
### Name
${build.name}
### Role
**${build.status}**`;

  // https://docs.airplane.dev/views/manually-executing-tasks
  // Load build info manually.

  const detailState = useComponentState("button");
  const detailResult = detailState.result

  console.log(detailResult)

  return (
    <Card>
      <Markdown>"hi"</Markdown>
      <Button id="button" task={{ slug: 'get_codebuild_build', params: params}}>
        Load details
      </Button>

      {detailResult && (
        <Markdown>{JSON.stringify(detailResult)}</Markdown>
      )}
    </Card>
  );
};


export default CodeBuildView;
