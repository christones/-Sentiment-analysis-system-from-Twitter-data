import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def client():
    from app.app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()
