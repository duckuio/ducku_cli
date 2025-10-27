import os
import traceback

def start(base):
    from src.use_cases.partial_lists import PartialMatch 
    from src.use_cases.pattern_search import PatternSearch
    from src.use_cases.unused_modules import UnusedModules
    from src.core.project import Project

    if not os.path.isdir(base):
        print(f"Path {base} doesn't exist")
        exit()
    try:
        use_cases_to_run = [
            PartialMatch,
            PatternSearch,
            UnusedModules
        ]
        p = Project(base)
        for uc in use_cases_to_run:
            uci = uc(p)
            if p.config.disabled_use_cases and uci.name in p.config.disabled_use_cases:
                continue
            r = uci.report()
            print(r)
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
                print(f"============ PROJECT {name} ==============")
                start(full_path)
    else:
        base = PROJECT_PATH if PROJECT_PATH else (input("Input the full path to the project: ")).strip()
        start(base)

# This allows the script to be run directly
if __name__ == "__main__":
    main()
