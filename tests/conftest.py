"""
Test fixtures ve yardımcı fonksiyonlar.
"""
from __future__ import annotations


import tempfile
import os
import pytest


@pytest.fixture
def temp_db():
    """Geçici SQLite veritabanı."""
    temp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp.close()
    yield temp.name
    os.unlink(temp.name)


@pytest.fixture
def mock_psutil_process():
    """Mock psutil.Process nesnesi."""
    class MockProcess:
        def __init__(self, pid=1234, name="test_process", cpu=10.0, mem=5.0):
            self.pid = pid
            self._name = name
            self._cpu = cpu
            self._mem = mem

        def name(self):
            return self._name

        def cpu_percent(self, interval=None):
            return self._cpu

        def memory_percent(self):
            return self._mem

        def terminate(self):
            pass

        def kill(self):
            pass

        def wait(self, timeout=None):
            pass

        def nice(self, value=None):
            return 0

    return MockProcess
