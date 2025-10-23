from pathlib import Path
from src.core.project import Project
from src.use_cases.partial import report

def test_partial_uc():
    path = Path(__file__).parent / ".." / "mocks" / "projects" / "parallel_entities"
    p = Project(path)
    report(p)