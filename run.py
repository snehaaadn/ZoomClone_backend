import uvicorn
import sys
import os
import types

backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(backend_dir, ".."))

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if "backend" not in sys.modules:
    backend_mod = types.ModuleType("backend")
    backend_mod.__path__ = [backend_dir]
    sys.modules["backend"] = backend_mod

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

