import sys
import os
import types

# When backend is run or cloned as an independent standalone repository,
# alias 'backend' to the parent of 'app' so all internal imports resolve seamlessly.
if "backend" not in sys.modules:
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    backend_mod = types.ModuleType("backend")
    backend_mod.__path__ = [backend_dir]
    sys.modules["backend"] = backend_mod
