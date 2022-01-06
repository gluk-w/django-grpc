from datetime import datetime

import pytest
from freezegun import freeze_time

from django_grpc.helpers.ratelimit import get_current_time_window


@pytest.mark.parametrize(
    "time_period,ts,expected",
    (
        (5, 1, 5),
        (5, 5, 5),
        (5, 6, 10),
        (10, 123, 130),
        (1, 123, 123),
    ),
)
def test_all_time_period_variations(time_period, ts, expected):
    with freeze_time(datetime.utcfromtimestamp(ts)):
        assert get_current_time_window(time_period) == expected
