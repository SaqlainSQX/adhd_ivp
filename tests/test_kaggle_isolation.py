import importlib.util
import os
from pathlib import Path


def test_project_credentials_and_proxy_changes_are_child_only(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "project_kaggle_launcher", Path(__file__).resolve().parents[1] / "scripts/kaggle_course.py"
    )
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    (tmp_path / "access_token").write_text("project-test-credential", encoding="utf-8")
    monkeypatch.setenv("KAGGLE_API_TOKEN", "other-account-test-credential")
    monkeypatch.setenv("KAGGLE_USERNAME", "other-account-test-user")
    monkeypatch.setenv("HTTPS_PROXY", "http://test-proxy.invalid")
    child, _ = launcher.isolated_environment(tmp_path, direct=True)
    assert child["KAGGLE_API_TOKEN"] == "project-test-credential"
    assert "KAGGLE_USERNAME" not in child
    assert "HTTPS_PROXY" not in child
    assert os.environ["KAGGLE_API_TOKEN"] == "other-account-test-credential"
    assert os.environ["HTTPS_PROXY"] == "http://test-proxy.invalid"
