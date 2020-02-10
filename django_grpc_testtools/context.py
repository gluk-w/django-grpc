from typing import Tuple


class FakeServicerContext:
    """
    Implementation of basic RpcContext methods that stores data
    for validation in tests
    """

    def __init__(self):
        self.abort_status = None
        self.abort_message = ""
        self._invocation_metadata = tuple()
        self._trailing_metadata = dict()

    def abort(self, status, message):
        """
        gRPC method that is called on RPC exit
        """
        self.abort_status = status
        self.abort_message = message
        raise Exception()  # Just like original context

    def set_trailing_metadata(self, items: Tuple[Tuple[str, str]]):
        """
        gRPC method that is called to set response metadata
        """
        self._trailing_metadata = {
            d[0]: d[1]
            for d in items
        }

    def get_trailing_metadata(self, key: str):
        """
        Helper to retrieve response metadata value by key
        """
        return self._trailing_metadata[key]

    def invocation_metadata(self) -> Tuple[Tuple[str, str]]:
        """
        gRPC method that retrieves request metadata
        """
        return self._invocation_metadata

    def set_invocation_metadata(self, items: Tuple[Tuple[str, str]]):
        """
        Helper to emulate request metadata
        """
        self._invocation_metadata = items

