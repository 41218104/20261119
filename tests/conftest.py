from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "xr_objects_test.db"
    monkeypatch.setenv("XR_DB_PATH", str(db_path))

    from app import storage

    storage.configure_db(db_path)
    storage.init_db()

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
