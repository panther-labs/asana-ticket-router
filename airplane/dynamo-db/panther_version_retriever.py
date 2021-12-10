# Linked to https://app.airplane.dev/t/get_panther_version [do not edit this line]
import re

from customer_info_retriever import retrieve_info


def get_version_from_template_url(line):
    version_with_v = re.search('s3.amazonaws.com/(.+?)/panther.yml', line).group(1)
    return version_with_v.lstrip("v")


def main(params):
    template_url = retrieve_info(
        fairytale_name=params["fairytale_name"],
        customer_query_keys=("PantherTemplateURL",)
    )
    return {"panther_version": get_version_from_template_url(template_url)}
