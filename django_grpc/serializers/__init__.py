from .base import BaseModelSerializer, message_to_python


def serialize_model(message_class, instance, serializers):
    """
    Shortcut
    """
    return BaseModelSerializer.serialize_model(message_class, instance, serializers)


def deserialize_message(message) -> dict:
    return message_to_python(message)
