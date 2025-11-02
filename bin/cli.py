import os
import traceback
from src.use_cases.partial_lists import PartialMatch 
from src.use_cases.pattern_search import PatternSearch
from src.use_cases.unused_modules import UnusedModules
from src.use_cases.spellcheck import Misspellings
from src.core.project import Project

# ANSI color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_GREEN = '\033[92m'

def colorized_title(text, color=Colors.BRIGHT_CYAN):
    """Create a colorized title with emoji and formatting."""
    return f"\n{Colors.BOLD}{color}🔍 {text}{Colors.RESET}\n" + "=" * (len(text) + 3) + "\n"

def start(base):
    if not os.path.isdir(base):
        print(f"Path {base} doesn't exist")
        exit()
    try:
        use_cases_to_run = [
            (PartialMatch, "Partial Match Detection"),
            (PatternSearch, "Pattern Search Analysis"), 
            (UnusedModules, "Unused Modules Detection"),
            (Misspellings, "Misspellings Detection"),
        ]
        p = Project(base)
        found = False
        for uc_class, title in use_cases_to_run:
            uci = uc_class(p)
            if p.config.disabled_use_cases and uci.name in p.config.disabled_use_cases:
                continue
            r = uci.report()
            if r != "":
                found = True
            print(colorized_title(title))
            if r and r.strip():  # Print the actual results
                print(r)
            else:  # No issues found
                print(f"{Colors.BRIGHT_GREEN}✅ No issues found{Colors.RESET}\n")
        if p.config.fail_on_issues and found:
            exit(1)
    except Exception as e:
        print(e)
        traceback.print_exc()

def main():
    """Entry point for the ducku CLI."""
    MULTI_FOLDER = os.getenv("MULTI_FOLDER")
    PROJECT_PATH = os.getenv("PROJECT_PATH")
    if MULTI_FOLDER:
        for name in os.listdir(MULTI_FOLDER):
            full_path = os.path.join(MULTI_FOLDER, name)
            if os.path.isdir(full_path):
                print(f"\n{Colors.BOLD}{Colors.BRIGHT_YELLOW}🏗️  PROJECT {name}{Colors.RESET}")
                print("=" * (len(name) + 12))
                start(full_path)
    else:
        base = PROJECT_PATH if PROJECT_PATH else (input("Input the full path to the project: ")).strip()
        start(base)

# This allows the script to be run directly
if __name__ == "__main__":
    main()
