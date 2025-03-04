from typing import NoReturn
from grpc import RpcError, StatusCode
from collections.abc import Sequence, Mapping

MetadataType = Sequence[tuple[str, str]]


class FakeServicerContext:
    """
    Implementation of basic RpcContext methods that stores data
    for validation in tests
    """

    def __init__(self):
        self.abort_status: StatusCode = StatusCode.UNKNOWN
        self.abort_message: str = ""
        self._invocation_metadata: MetadataType = tuple()
        self._trailing_metadata: Mapping[str, str] = dict()

    def abort(self, status: StatusCode, message: str) -> NoReturn:
        """
        gRPC method that is called on RPC exit
        """
        self.abort_status = status
        self.abort_message = message
        raise RpcError(message)  # Just like original context

    def set_trailing_metadata(self, items: MetadataType) -> None:
        """
        gRPC method that is called to set response metadata
        """
        self._trailing_metadata = {
            d[0]: d[1]
            for d in items
        }

    def get_trailing_metadata(self, key: str) -> str:
        """
        Helper to retrieve response metadata value by key
        """
        return self._trailing_metadata[key]

    def invocation_metadata(self) -> MetadataType:
        """
        gRPC method that retrieves request metadata
        """
        return self._invocation_metadata

    def set_invocation_metadata(self, items: MetadataType) -> None:
        """
        Helper to emulate request metadata
        """
        self._invocation_metadata = items