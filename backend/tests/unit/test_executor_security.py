"""Unit tests: RestrictedPython sandbox security (TDD – write first).

These tests verify that the sandbox prevents unauthorized filesystem and
network access while still permitting safe list comprehensions, builtins,
and arithmetic that legitimate collectors require.
"""
from __future__ import annotations

import pytest

from src.engine.executor import CodeExecutor


_EXECUTOR = CodeExecutor()


class TestSandboxSecurity:
    def test_file_open_is_blocked(self) -> None:
        code = """
result = open('/etc/passwd').read()
"""
        with pytest.raises(Exception):
            _EXECUTOR.run_code(code, {})

    def test_import_os_is_blocked(self) -> None:
        code = """
import os
result = os.listdir('.')
"""
        with pytest.raises(Exception):
            _EXECUTOR.run_code(code, {})

    def test_subprocess_is_blocked(self) -> None:
        code = """
import subprocess
result = subprocess.check_output(['id'])
"""
        with pytest.raises(Exception):
            _EXECUTOR.run_code(code, {})

    def test_safe_arithmetic_works(self) -> None:
        code = """
result = [x * 2 for x in range(5)]
"""
        result = _EXECUTOR.run_code(code, {})
        assert result == [0, 2, 4, 6, 8]

    def test_safe_dict_manipulation_works(self) -> None:
        code = """
data = [{"a": 1}, {"a": 2}]
result = [{"doubled": row["a"] * 2} for row in data]
"""
        result = _EXECUTOR.run_code(code, {})
        assert result == [{"doubled": 2}, {"doubled": 4}]

    def test_access_to_injected_globals(self) -> None:
        code = """
result = MY_VALUE + 1
"""
        result = _EXECUTOR.run_code(code, {"MY_VALUE": 41})
        assert result == 42
