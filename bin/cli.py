import os
import traceback

def start(base):
    from src.use_cases.partial import report as partial_report
    from src.use_cases.pattern_search import report as patterns_report
    from src.core.project import Project

    if not os.path.isdir(base):
        print(f"Path {base} doesn't exist")
        exit()
    try:
        ucases_to_run = [
            #partial_report,
            patterns_report
        ]
        p = Project(base)
        for uc in ucases_to_run:
            r = uc(p)
            print(r)
    except Exception as e:
        print(e)
        traceback.print_exc()

def main():
    """Entry point for the documentary CLI."""
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
