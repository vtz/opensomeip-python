# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

<!-- towncrier release notes start -->

## [0.1.1](https://github.com/vtz/opensomeip-python/releases/tag/v0.1.1) - 2026-03-13

### Bug Fixes

- Emit an `ImportWarning` when the C++ extension (`_opensomeip`) fails to load
  instead of silently degrading to no-op transport stubs. The warning includes
  the underlying error, a macOS-specific hint about libc++ ABI mismatches with
  Homebrew LLVM, and a link to the new Troubleshooting section in the README.

### Features

- Build and publish pre-compiled wheels for **Python 3.14** (added `cp314` to the
  cibuildwheel build matrix). Free-threaded builds (`*t-*`) are skipped until
  thread safety is validated.
- Add Python 3.14 to the CI test matrix.

### Documentation

- Add a Troubleshooting section to the README covering the macOS C++ extension
  load failure (`symbol not found in flat namespace`) and the silent no-op
  transport symptom.
