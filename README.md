# Ducku 

Ducku is a static documentation quality tool

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-DSAL-orange.svg)](LICENSE)

[ This documentation was checked by Ducku ]

**Ducku** is a documentation analysis and code quality CLI tool designed to help developers maintain clean, consistent, and up-to-date codebases. It automatically scans projects to identify issues like outdated documentation references, unused modules, and inconsistencies between code and documentation.

## 🚀 Use Cases

### 1. Pattern Search 🔍

Often documentation contains some outdated artifacts, like non-existing scripts and ports which have been changed.
Docku staticly detects certain patterns in documentation and checks their existance in the code.
Currently it supports:

- Filenames
- File paths (both Unix and Windows)
- Environment variables
- Ports


### 2. Partial Match Detection 🎯

Second frequent issue in documentation is partial lists. For example in this project there can be implemented a new use case, but it can be forgotten to document here.
So Ducku corresponds lists in documentation as
- headers
- bullet points

with potential lists in code as
- files/folders in one folder
- JSON/YAML keys/values at the same level

### 3. Unused Module Detection (beta)

This use case helps you to identify modules which are not imported from anywhere. 
That means one of:
- This module is an entry point (e.g CLI script or Docker endpoint)
- This module is obsolete

In the first case it should be documented, since it's direct instructions of using the system
In the second case likely deleted.

Languages support:

- Python
- JavaScript/TypeScript
- Java
- C#
- Go
- Ruby
- PHP


## Installation 📦

### Install from PyPI (Recommended)

```bash
pip install ducku
```

Then `ducku` binary will be available globally

### Using in CI/CD

Example of usage in CI/CD (GitLab):

```yaml
documentation_check:
    image: yarax/ducku:latest
    stage: quality
    variables:
        PROJECT_PATH: "$CI_PROJECT_DIR"
    script:
        - ducku
```

Example for GitHub Actions:

```yaml
- name: Documentation Quality Check
  run: |
    docker run --rm \
      -v ${{ github.workspace }}:/workspace \
      -e PROJECT_PATH=/workspace \
      yarax/ducku:latest
```

Also feel free to utilize [`Dockerfile`](Dockerfile) to build and use your own image.

## Usage 🚀

### Command Line Interface

#### Analyze a Single Project

Interactive mode

```bash
ducku
```

Use `PROJECT_PATH` environment variable to define the project root

```bash
PROJECT_PATH=/path/to/your/project ducku
```

#### Analyze Multiple Projects
```bash
MULTI_FOLDER=/path/to/projects/directory ducku
```

## ⚙️ Configuration

Create a `.ducku.yaml` file in your project root:

```yaml
# Disable specific use cases
disabled_use_cases:
# possible values
  - unused_modules
  - pattern_search
  - partial_lists

# Additional documentation paths
documentation_paths:
  - /tmp/other_docs

# Custom file patterns to skip
disabled_pattern_search_patterns:
# possible values
  - "Unix path"
  - "Windows path"
  - "Filename"
  - "Port Number"
  - "Environment variable"
```

## � Pre-commit Hook

You can integrate Ducku into your Git workflow using pre-commit hooks to automatically check documentation quality before commits.

1. **Install pre-commit**:
```bash
pip install pre-commit
```

2. **Create `.pre-commit-config.yaml`** in your repository root:
```yaml
repos:
  - repo: local
    hooks:
      - id: ducku
        name: Documentation Quality Check
        entry: ducku
        language: system
        pass_filenames: false
        always_run: true
        env:
          - PROJECT_PATH=.
```

3. **Install the hook**:
```bash
pre-commit install
```

## �🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`uv run pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Adding New Use Cases

To add a new analysis use case:

1. Create a new class inheriting from `BaseUseCase`
2. Implement the `report()` method
3. Add the use case to `bin/cli.py`
4. Write comprehensive tests

## 📝 License

This project is licensed under the Ducku Source Available License (DSAL) - see the [LICENSE](LICENSE) file for details.

**Key License Points:**
- ✅ Free for personal use, internal business use, and non-commercial purposes
- ✅ Educational and research use permitted
- ❌ Commercial documentation tools and services cannot use this software
- ❌ Cannot be integrated into paid documentation platforms
- 📖 Source code must remain available under the same license terms

For detailed terms and conditions, please review the full [LICENSE](LICENSE) file.