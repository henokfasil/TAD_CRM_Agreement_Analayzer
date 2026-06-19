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


def test_admin_codebook_rows_are_arrow_safe() -> None:
    module_globals = runpy.run_path(
        "streamlit_app/pages/12_Admin_and_Codebook.py",
        run_name="__streamlit_test__",
    )

    rows = module_globals["renderable_codebook_rows"]()

    assert rows
    assert all(
        not isinstance(value, (list, dict))
        for row in rows
        for value in row.values()
    )
