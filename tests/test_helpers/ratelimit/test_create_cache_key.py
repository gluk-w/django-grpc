import pytest

from django_grpc.helpers.ratelimit import create_cache_key


@pytest.mark.parametrize(
    "group,values,time_period,key",
    (
        # Check no error
        ("group1", ["127.0.0.1"], 10, "9dd03b92175234c2e5663ee679b75e80"),
        # Check group can be empty string
        ("", ["127.0.0.1"], 10, "ab127f240a67eac19964e8215f5b728e"),
        # Check values can be empty list
        ("group1", [], 10, "736e3d2817d361cc4bed726bd61a6cad"),
        # Check values can contain multiple values
        ("group1", ["1", "2", "3"], 10, "213369c345338900dc27974787c0d44f"),
    ),
)
def test_different_input_values(group, values, time_period, key):
    result = create_cache_key(group, values, time_period)
    assert result == key


@pytest.mark.parametrize(
    "group,values,time_period",
    (
        # Check time_period changed
        ("group1", ["127.0.0.1"], 11),
        # Check group changed
        ("", ["127.0.0.1"], 10,),
        # Check values changed
        ("group1", [], 10,),
        # Check values changed
        ("group1", ["1", "2", "3"], 10),
    ),
)
def test_hash_changes_when_input_changes(group, values, time_period):
    result = create_cache_key(group, values, time_period)
    # Key generated with create_cache_key("group1", ["127.0.0.1"], 10)
    assert result != "9dd03b92175234c2e5663ee679b75e80"
