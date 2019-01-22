#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
from time import sleep

import pytest
from django.core.management import call_command


def call_grpc_server_command(options):
    call_command("grpcserver", **options)


def test_management_command(mocker):
    mocker.patch.object('')

    srv = threading.Thread(target=call_grpc_server_command, args=[{"max_workers": 3, "port": 50080, "autoreload": False}])
    srv.start()
    sleep(5)

