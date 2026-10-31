#!/usr/bin/env python3
"""Regression test for OTA discovery prompt transport over stdin."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).with_name("discover-ota-workqueue.py")


class StdinTransportTest(unittest.TestCase):
    def test_run_passes_input_without_appending_to_argv(self):
        spec = importlib.util.spec_from_file_location("ota_discovery", SOURCE)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(module.subprocess, "run") as invoke:
                invoke.return_value.returncode = 0
                invoke.return_value.stdout = "ok"
                self.assertEqual(
                    module.run(["claude", "-p"], cwd=Path(tmp), input_text="prompt payload"),
                    "ok",
                )
                args, kwargs = invoke.call_args
                self.assertEqual(args[0], ["claude", "-p"])
                self.assertEqual(kwargs["input"], "prompt payload")
                self.assertTrue(kwargs["text"])


if __name__ == "__main__":
    unittest.main()
