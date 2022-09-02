from dataclasses import dataclass

from v2.pyshared.sf_client import parse_sql_results


class SfResultMock:

    def __init__(self, col_names, return_data):
        self.description = col_names
        self.return_data = return_data

    def fetchmany(self, _):
        return self.return_data


@dataclass
class SfResultColNameMock:
    name: str


def test_parse_sql_results():
    col_names = [SfResultColNameMock("col_name_1"), SfResultColNameMock("col_name_2")]
    return_data_mock = [["cell_1_1", "cell_1_2"], ["cell_2_1", "cell_2_2"]]
    result = SfResultMock(col_names=col_names, return_data=return_data_mock)
    data = parse_sql_results(result)

    assert len(data) == 2
    assert data[0]["col_name_1"] == "cell_1_1"
    assert data[0]["col_name_2"] == "cell_1_2"
    assert data[1]["col_name_1"] == "cell_2_1"
    assert data[1]["col_name_2"] == "cell_2_2"
