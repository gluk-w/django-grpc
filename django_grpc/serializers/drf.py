try:
    from google.protobuf.json_format import MessageToDict, ParseDict
    from rest_framework import serializers

    def _is_field_optional(field):
        """
        Checks if a field is optional.

        Under the hood, Optional fields are OneOf fields with only one field with the name of the OneOf
        prefixed with an underscore.
        """

        if not (co := field.containing_oneof):
            return False

        return len(co.fields) == 1 and co.name == f"_{field.name}"

    def message_to_dict(message, **kwargs):
        """
        Converts a protobuf message to a dictionary.
        Uses the default `google.protobuf.json_format.MessageToDict` function.
        Adds None values for optional fields that are not set.
        """

        kwargs.setdefault("including_default_value_fields", True)
        kwargs.setdefault("preserving_proto_field_name", True)

        result_dict = MessageToDict(message, **kwargs)
        optional_fields = {
            field.name: None
            for field in message.DESCRIPTOR.fields
            if _is_field_optional(field)
        }

        return {**optional_fields, **result_dict}

    def parse_dict(js_dict, message, **kwargs):
        kwargs.setdefault("ignore_unknown_fields", True)
        return ParseDict(js_dict, message, **kwargs)

    class GrpcSerializer(serializers.BaseSerializer):
        def __init__(self, *args, **kwargs):
            message = kwargs.pop("message", None)
            if message is not None:
                self._message = message
                kwargs["data"] = self.message_to_data(message)
            super().__init__(*args, **kwargs)

        @property
        def message(self):
            if not hasattr(self, "_message"):
                self._message = self.data_to_message(self.data)
            return self._message

        def message_to_data(self, message):
            """Protobuf message -> Dict of python primitive datatypes."""
            return message_to_dict(message)

        def data_to_message(self, data):
            """Protobuf message <- Dict of python primitive datatypes."""
            assert hasattr(
                self, "Meta"
            ), 'Class {serializer_class} missing "Meta" attribute'.format(
                serializer_class=self.__class__.__name__
            )
            assert hasattr(
                self.Meta, "proto_class"
            ), 'Class {serializer_class} missing "Meta.proto_class" attribute'.format(
                serializer_class=self.__class__.__name__
            )
            return parse_dict(data, self.Meta.proto_class())

except ImportError:
    pass
