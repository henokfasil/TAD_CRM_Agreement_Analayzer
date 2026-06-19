import runpy
import sys
from pathlib import Path


def test_streamlit_home_adds_project_root_for_cloud_imports() -> None:
    project_root = Path.cwd()
    original_path = list(sys.path)
    try:
        sys.path = [path for path in sys.path if path != str(project_root)]
        runpy.run_path("streamlit_app/Home.py", run_name="__streamlit_test__")
        assert str(project_root) in sys.path
    finally:
        sys.path = original_path
