import { Loader, Column, Stack, Table, Text, Title, Card, Markdown, Button, useTaskQuery, useComponentState } from "@airplane/views";

type AccountsRow = {
  accountID: string;
  organization: string;
};

const accountsColumn: Column[] = [
  {
    label: "AWS Account ID",
    accessor: "accountID",
  },
  {
    label: "Organization",
    accessor: "organization",
  },
];

type ProjectRow = {
  region: string;
  projectName: string;
};

const projectColumns: Column[] = [
  {
    label: "Project Name",
    accessor: "id",
  },
  {
    label: "Region",
    accessor: "region",
  },
];

type BuildRow = {
  name: string;
  status: string;
  timestamp: string;
};


const buildColumns: Column[] = [
  {
    label: "Name",
    accessor: "id",
  },
  {
    label: "Status",
    accessor: "status",
  },
  {
    label: "Completed",
    accessor: "complete",
  },
  {
    label: "Number",
    accessor: "number",
  },
  {
    label: "Start time",
    accessor: "startTime",
  },
  {
    label: "End Time",
    accessor: "endTime",
  },
  {
    label: "ARN",
    accessor: "arn",
  },
];

// Put the main logic of the view here.
// Views documentation: https://docs.airplane.dev/views/getting-started
const CodebuildView = () => {
  const accountsState = useComponentState("accounts");
  const selectedAccount = accountsState.selectedRow;

  const projectsState = useComponentState("projects");
  const selectedProject = projectsState.selectedRow;

  const buildsState = useComponentState("builds");
  const selectedBuild = buildsState.selectedRow;

  console.log(selectedAccount)
  console.log(selectedProject)
  console.log(selectedBuild)

  return (<>
    <Stack>
      <Title>CodeBuild</Title>
      <Text>Select your codebuild.</Text>
      <Table
        id="accounts"
        title="Accounts Table"
        columns={accountsColumn}
        task="list_accounts"
        rowSelection="single"
        defaultPageSize="5"
      />
    </Stack>

    {selectedAccount && (
        <Stack>
          <Table
            id="projects"
            title="Projects"
            columns={projectColumns}
            task={{slug: "list_codebuild_projects", refetchInterval: 60000, params: {
                aws_account_id: selectedAccount.accountID,
              }}}
            rowSelection="single"
            defaultPageSize="9"
          />
        </Stack>
      )}

    {selectedProject && (
        <Stack>
          <Table
            id="builds"
            title="Builds"
            columns={buildColumns}
            task={{slug: "list_codebuild_builds", refetchInterval: 60000, params: {
                aws_account_id: selectedAccount.accountID,
                region: selectedProject.region,
                project_name: selectedProject.id,
                count: 3,
              }}}
            rowSelection="single"
            defaultPageSize="3"
          />
          {selectedBuild && (
            <Stack direction="row" grow>
              <BuildDetail account={selectedAccount.accountID} region={selectedProject.region} project={selectedProject.id} build={selectedBuild} />
            </Stack>
          )}
        </Stack>
      )}
  </>);
};

const BuildDetail = ({ account, region, project, build }) => {
  const params = {
      aws_account_id: account,
      region: region,
      project_name: project,
      build: build.id
  };

  console.log('running query')

  const { output, loading, error, refetch } = useTaskQuery({
    slug: 'get_codebuild_build',
    params: params,
    executeOnMount: true,
  });


  const logs = output?.log || [];
  const startTime = output?.info?.startTime || 'N/A';
  const endTime = output?.info?.endTime || 'N/A';


  const summary = `##  _${build.id}_

Status:  **${build.status}**

Started: _${startTime}_

Ended: _${endTime}_

### Log
`;

  const fdate = (timestamp) => {
    console.log(timestamp)
    return new Intl.DateTimeFormat('en-US', {year: 'numeric', month: '2-digit',day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit'}).format(timestamp)
  }

  return (
    <Card>
      {loading && (<Loader variant="dots" />)}
      {error && (<>{error}</>)}
      {output && (
        <Markdown>{summary}</Markdown>
      )}
      {output && logs.map(({ ingestionTime, message }) => (
        <>
          <Text size='sm'>
            {fdate(ingestionTime)} - {message}
          </Text>
        </>
      ))}
    </Card>
  );
};

export default CodebuildView;
