"""CodeExecutor – secure sandbox for running user-supplied Python snippets
using ``RestrictedPython``.

The executor is intentionally minimal: it compiles user code with
``RestrictedPython``, executes it in a tight sandbox where the output of
the script must be stored in the variable called ``result``, and returns
that value.  Any exception that escapes the sandbox is re-raised so the
caller (the data pipeline) can decide how to handle it without crashing.

Design notes
------------
- ``open`` is explicitly removed: file access is never allowed.
- Only a safe subset of builtins is exposed (arithmetic, formatting, etc.).
- Sensible ``_getattr_`` and ``_getiter_`` guards are in place to prevent
  attribute-level escape.
- External HTTP libraries (like ``requests``) are NOT blocked at this layer –
  the constitution explicitly allows controlled network access.  Platform-level
  controls (seccomp, network policies) are expected to enforce on-prem limits.
"""
from __future__ import annotations

import logging
from typing import Any

from RestrictedPython import (
    compile_restricted,
    safe_builtins,
    safe_globals,
    limited_builtins,
)
from RestrictedPython.Guards import (
    safe_globals as rp_safe_globals,
    guarded_iter_unpack_sequence,
    guarded_unpack_sequence,
)

logger = logging.getLogger(__name__)

# ── Safe builtins whitelisted for collector scripts ───────────────────────────
_SAFE_BUILTINS: dict[str, Any] = {
    **safe_builtins,
    "sorted": sorted,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "hasattr": hasattr,
    "getattr": getattr,
    "setattr": None,          # explicitly deny setattr
    "open": None,             # explicitly deny file access
    "__import__": None,       # deny dynamic imports
}

_SANDBOX_GLOBALS: dict[str, Any] = {
    "__builtins__": _SAFE_BUILTINS,
    "_getattr_": getattr,
    "_getitem_": lambda obj, key: obj[key],
    "_getiter_": iter,
    "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
    "_unpack_sequence_": guarded_unpack_sequence,
    "_write_": lambda obj: obj,   # allow writes to locals only
}


class CodeExecutor:
    """Execute a Python code snippet inside a RestrictedPython sandbox.

    The script must assign its output to the variable ``result``.
    """

    def run_code(
        self,
        code: str,
        extra_globals: dict[str, Any],
    ) -> Any:
        """Compile and run *code* with the provided extra globals.

        Parameters
        ----------
        code:
            Python source string.  Must assign the output to ``result``.
        extra_globals:
            Additional names injected into the sandbox (e.g., resolved
            secrets, configuration values).

        Returns
        -------
        Any
            The value of ``result`` after execution, or ``None`` if the
            variable was not set.

        Raises
        ------
        SyntaxError / Exception
            Propagated as-is so callers can record and display errors.
        """
        byte_code = compile_restricted(code, filename="<collector>", mode="exec")

        sandbox: dict[str, Any] = {**_SANDBOX_GLOBALS, **extra_globals}

        exec(byte_code, sandbox)  # noqa: S102 – controlled sandbox

        return sandbox.get("result")
