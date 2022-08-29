from pyshared.airplane_utils import AirplaneTask
from pyshared.customer_info_retriever import retrieve_notion_account


class DeprovStatusUpdater(AirplaneTask):

    @staticmethod
    def main(params):
        key, val = params["deprov_key_val"].split("=")
        setattr(retrieve_notion_account(fairytale_name=params["fairytale_name"]), key.strip(), val.strip())


def main(params):
    return DeprovStatusUpdater().main(params)
