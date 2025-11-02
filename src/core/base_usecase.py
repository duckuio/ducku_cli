from src.core.project import Project


class BaseUseCase:
    def __init__(self, project: Project):
        self.project = project

    # Returns report or an empty string if nothing to report
    def report(self):
        raise NotImplementedError("Subclasses must implement the report method")