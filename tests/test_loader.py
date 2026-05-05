import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import tempfile
import csv
import os


def _write_sample_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def test_db_connection_uses_env(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "testhost")
    monkeypatch.setenv("POSTGRES_PORT", "5433")
    monkeypatch.setenv("POSTGRES_DB", "testdb")
    monkeypatch.setenv("POSTGRES_USER", "testuser")
    monkeypatch.setenv("POSTGRES_PASSWORD", "testpass")

    with patch("psycopg2.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        from loader import db
        import importlib
        importlib.reload(db)
        conn = db.get_connection()
        mock_connect.assert_called_once()
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs["host"] == "testhost"
        assert call_kwargs["port"] == 5433


def test_load_static_skips_missing_files(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    # Only create territories.csv, not the others
    territories_csv = tmp_path / "raw" / "static" / "territories.csv"
    _write_sample_csv(territories_csv, [
        {"territory_id": "abc", "territory_name": "T1", "region": "R1",
         "country": "US", "zone": "Z1"}
    ])
    with patch("loader.load_raw.get_connection") as mock_conn:
        mock_conn.return_value.__enter__ = MagicMock()
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        conn_obj = MagicMock()
        mock_conn.return_value = conn_obj
        conn_obj.cursor.return_value.__enter__ = MagicMock(return_value=MagicMock())
        conn_obj.cursor.return_value.__exit__ = MagicMock(return_value=False)
        # Should not raise even though most CSVs are missing
        import importlib
        import loader.load_raw as lr
        importlib.reload(lr)
        # Just verify it runs without exception for missing files
