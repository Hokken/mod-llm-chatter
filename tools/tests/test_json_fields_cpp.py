#!/usr/bin/env python3
"""Build and run the standalone C++ test for
src/LLMChatterJsonFields.h (the readers used by
IsProximityFightLineStillValid()).

The test is standard-library only and separate from the
server build. It needs a host C++ compiler (`CXX`, `c++`,
`g++`, or `clang++`); without one it is skipped and says so.

Run directly from the module root:
  python tools/tests/test_json_fields_cpp.py
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parents[2]
SOURCE = MODULE_DIR / "tools" / "tests" / "cpp" / "test_json_fields.cpp"
INCLUDE = MODULE_DIR / "src"


def find_compiler():
    candidates = [os.environ.get("CXX"), "c++", "g++", "clang++"]
    for name in candidates:
        if name and shutil.which(name):
            return shutil.which(name)
    return None


def test_fight_validity_uses_shared_readers():
    fight = (INCLUDE / "LLMChatterProximityFight.cpp").read_text(
        encoding="utf-8")
    body = fight.split(
        "bool IsProximityFightLineStillValid(", 1)[1]
    body = body.split("// Hooks (map worker threads)", 1)[0]
    assert "LLMChatterJson::ReadString(" in body
    assert "LLMChatterJson::ReadUInt64(" in body
    assert "ReadJsonString" not in fight
    assert "ReadJsonUInt" not in fight


def run_cpp_test() -> bool:
    compiler = find_compiler()
    if not compiler:
        print("SKIP: no host C++ compiler; C++ reader test not run")
        return True
    with tempfile.TemporaryDirectory() as tmp:
        exe = Path(tmp) / "test_json_fields"
        build = subprocess.run(
            [compiler, "-std=c++17", "-Wall", "-Wextra",
             "-I", str(INCLUDE), str(SOURCE), "-o", str(exe)],
            capture_output=True, text=True,
        )
        if build.returncode != 0:
            print(build.stdout + build.stderr)
            return False
        run = subprocess.run(
            [str(exe)], capture_output=True, text=True)
        print(run.stdout.strip())
        return run.returncode == 0


def main() -> int:
    test_fight_validity_uses_shared_readers()
    ok = run_cpp_test()
    if ok:
        print("OK")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
