from src.core.project import Project
from src.core.base_usecase import BaseUseCase
import codespell_lib
import io
from contextlib import redirect_stdout, redirect_stderr


class Misspellings(BaseUseCase):
    def __init__(self, project: Project):
        super().__init__(project)
        self.name = "spellcheck"

    def report(self):
        # Capture output from codespell
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Get all documentation files to check
        doc_files = []
        for dp in self.project.documentation.doc_parts:
            if dp.source.type == "file" and "path" in dp.source.metadata:
                doc_files.append(dp.source.metadata["path"])
        
        if not doc_files:
            return "No documentation files found to check for misspellings.\n"
        
        try:
            # Run codespell with captured output
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exit_code = codespell_lib.main(
                    '--ignore-words-list', 'Ducku,ducku',  # Ignore our project name
                    '--quiet-level', '2',  # Only show misspellings
                    *doc_files
                )
            
            output = stdout_capture.getvalue()
            error_output = stderr_capture.getvalue()
            
            if exit_code == 0 and not output:
                return ""
            elif output:
                return f"Misspellings found:\n{output}"
            elif error_output:
                return f"Error checking misspellings: {error_output}"
            else:
                return ""
                
        except (OSError, ValueError) as e:
            return f"Error running misspelling check: {str(e)}\n"