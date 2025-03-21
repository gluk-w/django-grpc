from datetime import datetime
from typing import NoReturn
from grpc import RpcError, StatusCode
from collections.abc import Sequence, Mapping
from grpc import ServicerContext

MetadataType = Sequence[tuple[str, str]]
_NON_OK_RENDEZVOUS_REPR_FORMAT = (
    "<{} of RPC that terminated with:\n"
    "\tstatus = {}\n"
    '\tdetails = "{}"\n'
    '\tdebug_error_string = "{}"\n'
    ">"
)


class FakeServicerContext(ServicerContext):
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
        debug_error_string = (
            "UNKNOWN:Error received from peer  "
            "{grpc_message:\"" + message + "\", "
            "grpc_status:" + str(status.value[0]) + ", "
            "created_time:\"" + str(datetime.now()) + "\"}"
        )
        stderr = _NON_OK_RENDEZVOUS_REPR_FORMAT.format(
            RpcError.__name__,
            status,
            message,
            debug_error_string,
        )
        raise RpcError(stderr)

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

    def set_code(self, code: StatusCode) -> None:
        self.abort_status = code

    def set_details(self, details: str) -> None:
        """Sets the value to be used as detail string upon RPC completion.

        This method need not be called by method implementations if they have
        no details to transmit.

        Args:
          details: A UTF-8-encodable string to be sent to the client upon
            termination of the RPC.
        """
        self.abort_message = details

    def code(self) -> StatusCode:
        """Accesses the value to be used as status code upon RPC completion.

        Returns:
          The StatusCode value for the RPC.
        """
        return self.abort_status

    def details(self) -> str:
        """Accesses the value to be used as detail string upon RPC completion.

        Returns:
          The details string of the RPC.
        """
        return self.abort_message

    def peer(self):
        raise NotImplementedError()

    def peer_identities(self):
        raise NotImplementedError()

    def peer_identity_key(self):
        raise NotImplementedError()

    def auth_context(self):
        raise NotImplementedError()

    def set_compression(self, compression):
        raise NotImplementedError()

    def send_initial_metadata(self, initial_metadata):
        raise NotImplementedError()

    def abort_with_status(self, status):
        raise NotImplementedError()

    def disable_next_message_compression(self):
        raise NotImplementedError()

    def is_active(self):
        raise NotImplementedError()

    def time_remaining(self):
        raise NotImplementedError()

    def cancel(self):
        raise NotImplementedError()

    def add_callback(self, callback):
        raise NotImplementedError()
