"""
AWS Lambda handler for Norrin.AI backend.

The FastAPI app now lives in `backend/app/main.py`.
This file bridges AWS Lambda → Mangum → FastAPI using the correct module path.

To deploy:
  cd backend
  pip install mangum
  # Package and upload to Lambda with handler: deployment.aws.lambda_handler.handler
"""
import sys
import os

# Ensure the backend/ directory is on the Python path when running in Lambda
_backend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, os.path.abspath(_backend_dir))

from app.main import app  # type: ignore[import]  # noqa: E402 – resolves via sys.path at runtime

try:
    from mangum import Mangum  # type: ignore[import]  # optional dep; install in Lambda layer
    handler = Mangum(app, lifespan="off")
except ImportError:
    # Mangum not installed — Lambda packaging not complete
    handler = None
