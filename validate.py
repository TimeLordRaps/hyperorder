"""Stream the bounded local field suite; this is not a VSTD certificate."""

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main() -> int:
    root = Path(__file__).resolve().parent
    if sys.version_info < (3, 12):
        raise SystemExit("Python 3.12 or later is required for this local runner")
    descriptor = json.loads((root / "FIELD.json").read_text(encoding="utf-8"))
    module = importlib.import_module(descriptor["module"])
    for name in descriptor["implementation_modules"]:
        implementation = importlib.import_module(name)
        if Path(implementation.__file__).resolve() != root / (name + ".py"):
            raise SystemExit("field implementation resolves outside this repository: " + name)
    missing = [name for name in descriptor["exports"] if not hasattr(module, name)]
    if missing:
        raise SystemExit(f"descriptor exports are unbound: {missing}")
    print(f"FULL SUITE {descriptor['field_id']}; overall deadline=20 seconds; "
          "no per-test isolation", flush=True)
    command = [sys.executable, "-u", "-m", "unittest", "discover", "-s", "tests",
               "-v", "--durations", "10"]
    try:
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run(command, cwd=root, timeout=20, check=False, env=environment).returncode
    except subprocess.TimeoutExpired:
        print("DEADLINE: owned test process terminated; outcome UNKNOWN", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
