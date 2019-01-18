=====
Usage
=====

To use Django gRPC in a project, add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'django_grpc.apps.DjangoGrpcConfig',
        ...
    )

Add Django gRPC's URL patterns:

.. code-block:: python

    from django_grpc import urls as django_grpc_urls


    urlpatterns = [
        ...
        url(r'^', include(django_grpc_urls)),
        ...
    ]
