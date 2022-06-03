import requests
import datetime

from pyshared.airplane_utils import AirplaneTask
from pyshared.aws_secrets import get_secret_value

SNYK_ORG_ID = "2150dee5-a6f2-4ef7-8da2-a97f009ec2b7"
ASANA_ORG = "1159526352574257"
VULN_PROJ_ID = "1201845336228686"   # https://app.asana.com/0/1201845336228686/list
ASANA_CF_SNYK_ID = "1201845398081566"
ASANA_CF_VULN_PACKAGE = "1202063552113550"
ASANA_CF_PROJ_NAME = "1202063552113548"
ASANA_CF_SNYK_SCORE = "1202063552113557"
ASANA_CF_FINDING_TYPE = "1202063552113554"


class SnykAsanaIntegration(AirplaneTask):
    @staticmethod
    def get_secrets():
        return (get_secret_value("airplane/security-snyk-token"),get_secret_value("airplane/security-asana-vuln-proj"))


    @staticmethod
    def build_endpoint_headers(endpoint, token):
        return (endpoint, {"Content-Type": "application/json","Authorization": token})

    def get_snyk_projects(self, snyk_token):
        vulnerable_projects = []

        endpoint, headers = self.build_endpoint_headers(f"https://snyk.io/api/v1/org/{SNYK_ORG_ID}/projects", f"token {snyk_token}")

        response = requests.get(endpoint, headers=headers).json()

        if not response:
            raise RuntimeError("Unexpected response from Snyk: " + response)

        for project in response.get("projects"):
            if project.get("isMonitored") and project.get("type") != "sast":
                name = project.get("name")
                type = project.get("type")
                issues = project.get("issueCountsBySeverity")

                if( issues.get("low") != 0 or
                    issues.get("medium") != 0 or
                    issues.get("high") != 0 or
                    issues.get("critical") != 0
                ):
                    print(name)
                    print(type)
                    print(issues)
                    print("-" * 32)

                    vulnerable_projects.append(project)

        return vulnerable_projects

    ## Currently we only create tasks for critical and high severity vulns. This can be adjusted here.
    def get_issues_per_project(self, project_id, snyk_token):
        endpoint, headers = self.build_endpoint_headers(f"https://snyk.io/api/v1/org/{SNYK_ORG_ID}/project/{project_id}/aggregated-issues", f"token {snyk_token}")
        data = {
                    "includeDescription": True,
                    "includeIntroducedThrough": True,
                    "filters": {
                        "severities": [
                            "critical",
                            "high"
                        ],
                        "exploitMaturity": [
                            "mature",
                            "proof-of-concept",
                            "no-known-exploit",
                            "no-data"
                        ],
                        "types": [
                            "vuln",
                            "license"
                        ],
                        "ignored": False,
                        "patched": False,
                        "priority": {
                            "score": {
                                "min": 0,
                                "max": 1000
                            }
                        }
                    }
                }

        response = requests.post(endpoint, headers=headers, json=data).json()

        if not response:
            raise RuntimeError("Unexpected response from Snyk: " + response)

        return response.get("issues")

    def dedup_asana_tasks(self, issues, asana_pat):
        deduped_issues = []

        for issue in issues:
            if self.asana_task_doesnt_exist(issue.get("id"), asana_pat):
                deduped_issues.append(issue)
        return deduped_issues

    def asana_task_doesnt_exist(self, issue_id, asana_pat):
        endpoint, headers = self.build_endpoint_headers(
            f"https://app.asana.com/api/1.0/workspaces/{ASANA_ORG}/tasks/search?custom_fields.1201845398081566.value={issue_id}",
            f"Bearer {asana_pat}")

        response = requests.get(endpoint, headers=headers).json()
        if not response.get("data"):
            return True
        elif response.get("data")[0].get('gid') != None:
            return False
        else:
            raise RuntimeError("Unexpected response from Asana: " + response)

    def create_asana_tasks(self, deduped_issues, asana_pat, project_name, project_type):
        endpoint, headers = self.build_endpoint_headers("https://app.asana.com/api/1.0/tasks", f"Bearer {asana_pat}")

        project_name = project_name.split("panther-labs/",1)[1]

        for issue in deduped_issues:
            snyk_id = issue.get("id")
            snyk_score = str(issue.get("priorityScore"))
            finding_type = issue.get("issueData").get("title")
            vuln_package = issue.get("pkgName")
            snyk_research_url = issue.get("issueData").get("url")
            vuln_desc = issue.get("issueData").get("description")
            exploit_maturity = issue.get("issueData").get("exploitMaturity")
            is_fixable = str(issue.get("isFixable"))
            current_version = issue.get("pkgVersions")[0]
            fixed_version = issue.get("fixedIn")
            snyk_console_link = issue.get("links").get("paths")


            task_name = ("[" + project_name + "][" + str(issue.get("priorityScore")) +
                            "] " + issue.get("issueData").get("title") + ": " + issue.get("pkgName"))
            due_on = str(datetime.date.today() + datetime.timedelta(days=7))

            html_body = (   f"<body>"
                            f"<b>Current Version:</b> {current_version}\n"
                            f"<b>Fixed Version:</b> {fixed_version}\n"
                            f"<b>Is Fixable:</b> {is_fixable}\n"
                            f"<b>Exploit Maturity:</b> {exploit_maturity}\n"
                            f"<b>Console Link:</b> <a href=\"{snyk_console_link}\"></a>\n"
                            f"<b>Additional details:</b> <a href=\"{snyk_research_url}\"></a>\n"
                            # removing since it can cause task creation errors due to embedded HTML & MD
                            #f"<b>Description:</b> {vuln_desc}\n"
                            f"</body>"
                        )

            # build the payload
            data = {
                        "data": {
                            "completed": False,
                            "custom_fields": {
                                ASANA_CF_SNYK_ID: snyk_id,  #Snyk finding ID
                                ASANA_CF_VULN_PACKAGE: vuln_package,  #vuln package
                                ASANA_CF_PROJ_NAME: project_name,  #vuln repo
                                ASANA_CF_SNYK_SCORE: snyk_score,  #snyk score
                                ASANA_CF_FINDING_TYPE: finding_type   #finding type
                            },
                            "due_on": due_on,
                            "html_notes": html_body,
                            "name": task_name,
                            "projects": [
                                VULN_PROJ_ID
                            ],
                            "memberships": [
                                {
                                    "project": VULN_PROJ_ID,
                                    "section": "1201845336228689", #Security Triage section of the vuln project
                                }
                            ],
                            "resource_subtype": "default_task",
                        }
                    }
            print("   [*] " + task_name)
            response = requests.post(endpoint, headers=headers, json=data).json()
            if response.get("errors"):
                raise RuntimeError("Unexpected response from Asana: " + response)
            elif not response:
                raise RuntimeError("Unexpected response from Snyk: " + response)

    def main(self, params):
        snyk_token, asana_pat = self.get_secrets()

        print("[+] Finding vulnerable projects")
        vulnerable_projects = self.get_snyk_projects(snyk_token)

        for project in vulnerable_projects:
            print("[+] Deduplicating existing issues for " + project.get("name"))
            issues = self.get_issues_per_project(project.get("id"), snyk_token)
            deduped_issues = self.dedup_asana_tasks(issues, asana_pat)
            print("[+] Creating issues for project " + project.get("name"))
            self.create_asana_tasks(deduped_issues, asana_pat, project.get("name"), project.get("type"))

    def cli(self):
        self.main({})

    def get_failure_slack_channel(self):
        return "#security-on-call"


def main(_):
    return SnykAsanaIntegration().main_notify_failures({})


if __name__ == "__main__":
    SnykAsanaIntegration().cli()
