from google.protobuf.message import Message
# from google.protobuf.pyext._message import RepeatedCompositeContainer

from typing import Iterable
from django.db.models import ForeignKey
from django.db.models.fields.reverse_related import ForeignObjectRel


class BaseModelSerializer:
    def __init__(self, model_class, serializers=None):
        self.model_class = model_class
        self.serializers = serializers

    def _to_dict(self, grpc_fields, instance):
        return {
            name: self._get_field_value(grpc_field, name, instance)
            for name, grpc_field in grpc_fields
        }

    def _get_field_value(self, grpc_field, name, instance):
        if instance is None:
            return None

        # Check if child serializer has special handling method
        method = getattr(self, "get_" + name, None)
        if method:
            return method(instance)

        # Default behaviour
        field_value = getattr(instance, name)
        field_meta = instance._meta.get_field(name)
        if isinstance(field_meta, ForeignObjectRel):
            return self._serialize_model_relations(grpc_field, field_value.all(), self.serializers)
        elif isinstance(field_meta, ForeignKey):
            return self.serialize_model(
                self.get_grpc_message_class(grpc_field),
                field_value,
                self.serializers
            )
        else:
            return field_value

    @classmethod
    def find_for_model(cls, instance, serializers: Iterable):
        serializer_candidates = [s for s in serializers if isinstance(instance, s.model_class)]
        return serializer_candidates[0] if len(serializer_candidates) else cls(instance.__class__, serializers)

    @classmethod
    def serialize_model(cls, message_class, instance: 'Model', serializers):
        serializer = cls.find_for_model(instance, serializers)
        serializer.serializers = serializers
        return message_class(**serializer._to_dict(message_class.DESCRIPTOR.fields_by_name.items(), instance))

    @classmethod
    def _serialize_model_relations(cls, grpc_field, related_items, serializers):
        message_class = cls.get_grpc_message_class(grpc_field)
        return [
            cls.serialize_model(message_class, it, serializers)
            for it in related_items
        ]

    @classmethod
    def get_grpc_message_class(cls, grpc_field):
        return grpc_field.message_type._concrete_class


def message_to_python(message) -> dict:
    """
    Convert fields in gRPC message to a dict
    """
    return {
        field.name: _message_value(val)
        for field, val in message.ListFields()
    }


def _message_value(val):
    """
    Check if nested values need to be deserialized
    """
    class_name = val.__class__.__name__
    # List of structures
    # Convert repeated
    # if isinstance(val, RepeatedCompositeContainer):
    if class_name == 'RepeatedCompositeContainer':
        return [
            message_to_python(it)
            for it in val
        ]
    # List of simple types
    if class_name == 'RepeatedScalarContainer':
        return list(val)

    # Convert single complex type (structure)
    if isinstance(val, Message):
        return message_to_python(val)

    # Simple type (str, int, bool)
    return val
