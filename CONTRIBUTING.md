# Contributing to opensomeip-python

Thank you for your interest in contributing! This guide covers the development
workflow, coding standards, and pull request process.

## Development Setup

```bash
# Clone with the C++ submodule
git clone --recurse-submodules https://github.com/vtz/opensomeip-python.git
cd opensomeip-python

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Building the C++ extension

The C++ extension requires CMake >= 3.20 and a C++17 compiler:

```bash
# The extension is built automatically by pip install
pip install -e ".[dev]"

# Or build manually with CMake
cmake -B build -S . -DCMAKE_BUILD_TYPE=Debug
cmake --build build
```

On macOS, if you encounter linker errors related to `libc++`, ensure you use
the system compiler:

```bash
CC=/usr/bin/clang CXX=/usr/bin/clang++ pip install -e ".[dev]"
```

## Running Tests

```bash
# Run all tests
pytest

# Run unit tests only (fast, no C++ extension required)
PYTHONPATH=src pytest tests/unit/

# Run with coverage
pytest --cov=opensomeip --cov-report=html

# Run property-based tests
pytest tests/property/
```

## Code Quality

### Linting and formatting

We use [ruff](https://docs.astral.sh/ruff/) for both linting and formatting:

```bash
ruff check src/ tests/       # lint
ruff check --fix src/ tests/  # auto-fix
ruff format src/ tests/       # format
```

### Type checking

All code must pass [mypy](https://mypy-lang.org/) in strict mode:

```bash
mypy src/opensomeip/
```

## Coding Standards

- **Python >= 3.10** — use modern syntax (`X | Y` unions, `match`, etc.)
- **Type annotations** on all public functions and methods
- **Docstrings** on all public classes and functions (Google style)
- **No unnecessary comments** — code should be self-explanatory; only document
  non-obvious intent, trade-offs, or constraints
- **dataclasses** for value types, **enums** for fixed sets of values
- **Context managers** for lifecycle management (`__enter__`/`__exit__`)

## Project Structure

```
src/
  opensomeip/        # Pure Python package (public API)
  _opensomeip/       # pybind11 C++ bindings (internal)
tests/
  unit/              # Unit tests (no network, no C++ extension required)
  property/          # Hypothesis property-based tests
  integration/       # Integration tests (require C++ extension + network)
extern/
  opensomeip/        # C++ SOME/IP stack (git submodule)
docs/                # Sphinx documentation
```

## Pull Request Process

1. **Fork** and create a feature branch from `main`
2. **Write tests** — aim for the existing coverage threshold (90%+)
3. **Add a changelog fragment** in `changes/` using
   [Towncrier](https://towncrier.readthedocs.io/):

   ```bash
   # For a new feature:
   echo "Description of the feature." > changes/feature/short-name.md

   # For a bug fix:
   echo "Description of the fix." > changes/bugfix/short-name.md

   # For a breaking change:
   echo "Description of the breaking change." > changes/breaking/short-name.md
   ```

4. **Ensure CI passes** — `ruff check`, `ruff format --check`, `mypy`, `pytest`
5. **Open a PR** against `main` with a clear description of the changes

## Updating the opensomeip Submodule

When a new version of the C++ library is released:

```bash
cd extern/opensomeip
git fetch origin
git checkout <new-tag>
cd ../..
git add extern/opensomeip
git commit -m "chore: update opensomeip to <new-tag>"
```

Then check if any C++ binding updates are needed in `src/_opensomeip/`.

## Release Process

Releases are automated via GitHub Actions:

1. Update the version in `pyproject.toml` and `docs/conf.py`
2. Run `towncrier build --version <version>` to generate release notes
3. Commit and tag: `git tag v<version>`
4. Push the tag: `git push origin v<version>`
5. Create a GitHub Release from the tag — this triggers wheel builds and PyPI publish

## License

By contributing, you agree that your contributions will be licensed under the
Apache License 2.0.
