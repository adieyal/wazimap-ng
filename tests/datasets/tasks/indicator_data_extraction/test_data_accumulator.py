import pytest

from wazimap_ng.datasets.tasks.indicator_data_extraction import DataAccumulator

@pytest.fixture
def data_accumulator():
    geography_id = 4
    return DataAccumulator(geography_id)

def test_subindicators_no_groups(data_accumulator):
    data = [
        {"age group": "15-19", "count": 21.0},
        {"age group": "20-24", "count": 41.0},
        {"age group": "25-29", "count": 61.0}
    ]

    data_accumulator.add_subindicator_data(data)

    assert data_accumulator.subindicators_data == [
        {"subindicator": "15-19", "count": 21.0},
        {"subindicator": "20-24", "count": 41.0},
        {"subindicator": "25-29", "count": 61.0},
    ]

def test_subindicators_with_groups(data_accumulator):
    data = [
        {"age group": "15-19", "gender": "male", "count": 20.0},
        {"age group": "20-24", "gender": "male", "count": 40.0},
        {"age group": "25-29", "gender": "male", "count": 60.0},
        {"age group": "15-19", "gender": "female", "count": 21.0},
        {"age group": "20-24", "gender": "female", "count": 41.0},
        {"age group": "25-29", "gender": "female", "count": 61.0}
    ]

    data_accumulator.primary_group = "gender"
    data_accumulator.add_subindicator_data(data)

    assert data_accumulator.subindicators_data == [
        {
            "group": "male",
            "values": [
                {"subindicator": "15-19", "count": 20.0},
                {"subindicator": "20-24", "count": 40.0},
                {"subindicator": "25-29", "count": 60.0},
            ]
        },
        {
            "group": "female",
            "values": [
                {"subindicator": "15-19", "count": 21.0},
                {"subindicator": "20-24", "count": 41.0},
                {"subindicator": "25-29", "count": 61.0},
            ]
        }
    ]

def test_add_groups_data(data_accumulator):
    data = [
        {"age group": "15-19", "gender": "female", "count": 20.0},
        {"age group": "20-24", "gender": "female", "count": 40.0},
        {"age group": "25-29", "gender": "female", "count": 60.0},
        {"age group": "15-19", "gender": "male", "count": 21.0},
        {"age group": "20-24", "gender": "male", "count": 41.0},
        {"age group": "25-29", "gender": "male", "count": 61.0}
    ]


    assert len(data_accumulator.groups_data) == 0

    data_male = [{"age group": x["age group"], "count": x["count"]} for x in data if x["gender"] == "male"]
    data_female = [{"age group": x["age group"], "count": x["count"]} for x in data if x["gender"] == "female"]

    data_accumulator.add_groups_data("gender", "female", {"data": data_female })

    assert len(data_accumulator.groups_data) == 1
    assert len(data_accumulator.groups_data["gender"]) == 1
    assert data_accumulator.groups_data["gender"]["female"] == [
        {"subindicator": "15-19", "count": 20},
        {"subindicator": "20-24", "count": 40},
        {"subindicator": "25-29", "count": 60},
    ]

    data_accumulator.add_groups_data("gender", "male", {"data": data_male})

    assert len(data_accumulator.groups_data) == 1
    assert len(data_accumulator.groups_data["gender"]) == 2
    assert data_accumulator.groups_data["gender"]["male"] == [
        {"subindicator": "15-19", "count": 21},
        {"subindicator": "20-24", "count": 41},
        {"subindicator": "25-29", "count": 61},
    ]


def test_get_groups(data_accumulator):
    data = [
        {"count": 23, "gender": "male", "age group": "15-19"},
        {"count": 46, "gender": "male", "age group": "20-24"},
        {"count": 23, "gender": "female", "age group": "15-19"},
    ]

    data_accumulator.primary_group = "gender"
    groups = data_accumulator.get_groups(data)

    assert len(groups) == 2
    assert "gender" in groups
    assert "age group" in groups