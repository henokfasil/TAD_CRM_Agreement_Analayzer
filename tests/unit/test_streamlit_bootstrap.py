from pathlib import Path

from streamlit_app.bootstrap import ensure_project_root_on_path


def test_streamlit_bootstrap_adds_project_root() -> None:
    project_root = ensure_project_root_on_path()
    assert project_root == Path.cwd()

