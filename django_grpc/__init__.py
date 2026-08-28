from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("django-grpc")
except PackageNotFoundError:  # running straight from a source checkout
    __version__ = "0.0.0+unknown"
