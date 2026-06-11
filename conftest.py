import os
import sys
import threading
import time
from pathlib import Path

import pytest
import requests
import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from db.database import init_db
from utils.api_client import APIClient

TEST_DB_PATH = PROJECT_ROOT / "data" / "test_ecommerce.db"
API_HOST = "127.0.0.1"
API_PORT = 8765
BASE_URL = f"http://{API_HOST}:{API_PORT}"


@pytest.fixture(scope="session")
def test_db() -> Path:
    db_path = init_db(TEST_DB_PATH, force_seed=True)
    os.environ["ECOMMERCE_DB_PATH"] = str(db_path)
    yield db_path
    if db_path.exists():
        db_path.unlink()


@pytest.fixture(scope="session")
def api_server(test_db: Path):
    config = uvicorn.Config(
        "mock_api.main:app",
        host=API_HOST,
        port=API_PORT,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.2)
    else:
        pytest.fail("Mock API server failed to start within 10 seconds")

    yield BASE_URL
    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture(scope="session")
def api_client(api_server: str) -> APIClient:
    return APIClient(api_server)
