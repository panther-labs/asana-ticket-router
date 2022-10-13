""" Submit release testing metrics to datadog """

from datetime import datetime

import asana
from pyshared.aws_secrets import get_secret_value
from pyshared.datadog.metric import DatadogMetric, Metric


class Asana():
    """ Connect to asana and get task metrics """

    def __init__(self, version, workspace=None):
        token = get_secret_value("airplane/deployment-asana-release-testing")
        self.workspace = workspace
        self.version = version
        self.client = asana.Client.access_token(token)

    def get_count(self):
        """ Return the number of tasks for bugs blocking release """

        project_id = self.get_project()
        section_id = self.get_section(project_id)
        tasks = self.get_tasks(section_id)
        return len(tasks)

    def get_project(self):
        """ Get project ID for target version """

        params={"resource_type": "project", "query": f"Release Testing - {self.version}"}
        project = self.client.typeahead.typeahead_for_workspace(self.workspace, params)
        return next(project)["gid"]

    def get_section(self, project_id):
        """ Get project section ID for bugs blocking release """

        sections = self.client.sections.get_sections_for_project(project_id)

        try:
            return next(filter(lambda s: "Bugs Blocking Release" in s["name"], sections))["gid"]
        except StopIteration:
            raise Exception(f"No section named Bugs Blocking Release found for project {project_id}")

    def get_tasks(self, section_id):
        """ Get list of tasks for bugs blocking release """

        return list(self.client.tasks.get_tasks_for_section(section_id))

def main(params):
    """ Gather metrics and submit to datadog """

    workspace = params["workspace"]
    version = params["version"]
    tasks_blocking_release = Asana(version=version, workspace=workspace).get_count()
    datadog = DatadogMetric(api_key=get_secret_value("airplane/datadog-api-key"))

    metric = {
        "name": "panther.BugsBlockingRelease",
        "type": "gauge",
        "points": [{"timestamp": int(datetime.now().timestamp()), "value": tasks_blocking_release}],
        "tags": [f"panther_version:{version}"],
    }

    datadog.submit(Metric(**metric))

    return {"panther_version": version, "num_blocking_bugs": tasks_blocking_release}
