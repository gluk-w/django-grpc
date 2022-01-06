import hashlib
import time
from functools import reduce
from typing import Callable, List, Optional, Tuple, Union

from functools import wraps

import grpc
from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured


def get_current_time_window(time_period: int):
    """Calculates end of the current time window for a given time period."""
    ts = int(time.time())
    if time_period == 1:
        return ts
    w = ts - (ts % time_period)
    if w < ts:
        return w + time_period
    return w


def create_cache_key(group: str, values: List[str], time_window: int):
    """Creates storage key for specified group and values of current time_period."""
    parts = [group, ".".join(values), str(time_window)]
    return hashlib.md5(''.join(parts).encode('utf-8')).hexdigest()


def get_keys_values(request, context, keys: List[Union[str, Callable]]) -> List[str]:
    values = []
    for key in keys:
        # User provided function to get key from request and context
        if callable(key):
            values.append(key(request, context))
        # Gets keys value from gRPCs message
        elif key.startswith("request:"):
            _, fields_dot_path = key.split(":")
            value = str(reduce(lambda msg, field: getattr(msg, field, ""), fields_dot_path.split("."), request))
            values.append(value)
        # Gets keys value from gRPCs metadata
        elif key.startswith("metadata:"):
            _, metadata_key = key.split(":")
            value = dict(context.invocation_metadata()).get(metadata_key, "") or ""
            values.append(value)

    return values


def save_call(cache_key: str, time_period: int) -> int:
    """Saves current call and returns number of calls for given key."""
    cache_name = getattr(settings, 'RATELIMIT_USE_CACHE', 'default')
    cache = caches[cache_name]

    count = 1
    # Extend the expiration time by a few seconds to avoid misses.
    added = cache.add(cache_key, count, time_period + 3)
    if not added:
        try:
            # memcached will throw a ValueError if server unavailable or key does not exist.
            count = cache.incr(cache_key)
        except ValueError:
            pass

    return count


def record_call(
    rpc,
    request,
    context,
    time_period: int,
    group: str = None,
    keys: List[Union[str, Callable]] = None,
) -> Tuple[int, int]:
    """Records call and returns current calls count.

    :param rpc: gRPCs procedure
    :param context: gRPCs context
    :param request: gRPCs message
    :param time_period: Time period per which limit calls
    :param group: Name of a group of ratelimits to count together.
        Basically to share the same ratelimit across one or more RPCs.
    :param keys: Client/s identifier. Like `group` but is used to group calls based on gRPCs message and context.
        For example by clients user-agent, ip and other requests information.
    :returns: Current count of calls and time left in seconds until enf of time period
    """
    if group is None:
        # By default group will be RPCs class' and methods name
        group = rpc.__qualname__
    if keys is None:
        keys = []

    if time_period <= 0:
        raise ImproperlyConfigured('time_period must be greater than 0')

    time_window = get_current_time_window(time_period)
    values = get_keys_values(request, context, keys)

    cache_key = create_cache_key(group, values, time_window)
    count = save_call(cache_key, time_period)

    time_left = time_window - int(time.time())
    return count, time_left


def ratelimit(max_calls: int, time_period: int, group: Optional[str] = None, keys: List[Union[str, Callable]] = None):
    """
    :param max_calls: Max number of calls in specified `time_period`.
    :param time_period: Time period in seconds per which limit `max_calls`.
    :param group: Name of a group of ratelimits to count together.
        Basically to share the same ratelimit across one or more RPCs.
    :param keys: Client/s identifier. Like `group` but is used to group calls based on gRPCs message and context.
        For example by clients user-agent, ip and other requests information.
    """

    def decorator(fn):
        @wraps(fn)
        def _wrapped(self, request, context):
            current_calls, time_left = record_call(fn, request, context, time_period, group, keys)

            if current_calls > max_calls:
                details = (f"Reached limit of {max_calls} calls per {time_period} seconds."
                           f" Resource will be available in {time_left} seconds.")
                context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, details)

            return fn(self, request, context)

        return _wrapped

    return decorator
