import pytest
import os
import subprocess
import time

@pytest.fixture(scope="session", autouse=True)
def start_zbx_server (request):
    zbx_cmd = [
        'python',
        'tests/ZabbixServerTrapper.py'
    ]
    zbx_proc = subprocess.Popen(zbx_cmd,
        stdout=open(os.devnull),
        stderr=open(os.devnull),
        shell=False
    )
    request.addfinalizer(zbx_proc.kill)
    time.sleep(0.5)
