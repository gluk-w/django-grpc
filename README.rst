=============================
Django gRPC
=============================

.. image:: https://badge.fury.io/py/django-grpc.svg
    :target: https://badge.fury.io/py/django-grpc

.. image:: https://travis-ci.org/gluk-w/django-grpc.svg?branch=master
    :target: https://travis-ci.org/gluk-w/django-grpc

.. image:: https://codecov.io/gh/gluk-w/django-grpc/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/gluk-w/django-grpc

Easy gRPC service based on Django application

Documentation
-------------

The full documentation is at https://django-grpc.readthedocs.io.

Quickstart
----------

Install Django gRPC::

    pip install django-grpc

Add it to your `INSTALLED_APPS`:

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

Features
--------

* TODO

Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox

Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
