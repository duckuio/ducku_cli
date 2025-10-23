# Deprecated in favor of pathlib.Path

from pathlib import Path

class File:
    def __init__(self, full_path):
        self.full_path = full_path
        self.p = Path(full_path)
        self.content = None
        self.name = self.p.name
        self.extension = self.p.suffix.lower()
        self.name_no_ext = self.p.stem
        # if project:
        #     try:
        #         self.relative_path = str(self.path.relative_to(Path(project.project_root)))
        #     except Exception:
        #         self.relative_path = None
        # else:
        #     self.relative_path = None

    def read(self):
        if self.content is not None:
            return self.content
        self.content = self.p.read_text(encoding="utf-8")
        return self.content

    def __str__(self):
        return str(self.path)

    def __repr__(self):
        return str(self.path)
