from django.core.cache import cache

from django_grpc.helpers.ratelimit import save_call


def test_add_new_call(clear_cache):
    key = "key"
    count = save_call(key, 10)

    # Check count
    assert count == 1

    # Check key exist in cache
    assert cache.get(key) == 1


def test_add_increment_existing_call(clear_cache):
    key = "key"
    count = save_call(key, 10)

    # Check count
    assert count == 1

    # Check key exist in cache
    assert cache.get(key) == 1

    count1 = save_call(key, 10)

    # Check count
    assert count1 == 2

    # Check key exist in cache
    assert cache.get(key) == 2


def test_add_different_keys(clear_cache):
    key = "key"
    count = save_call(key, 10)

    # Check count
    assert count == 1

    # Check key exist in cache
    assert cache.get(key) == 1

    key1 = "key1"
    count1 = save_call(key1, 10)

    # Check count
    assert count1 == 1

    # Check key exist in cache
    assert cache.get(key1) == 1
