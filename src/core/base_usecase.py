from src.core.project import Project


class BaseUseCase:
    def __init__(self, project: Project):
        self.project = project

    def report(self):
        raise NotImplementedError("Subclasses must implement the report method")