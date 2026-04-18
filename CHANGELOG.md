# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

<!-- towncrier release notes start -->

## [0.1.4](https://github.com/vtz/opensomeip-python/releases/tag/v0.1.4) - 2026-04-18

### Features

- Add optional `remote_endpoint` field to `ClientConfig`, enabling
  communication with SOME/IP servers that do not run Service Discovery.
  The transport layer already supported static remote endpoints — this
  wires the option through the high-level client configuration.

### Miscellaneous

- Bump `softprops/action-gh-release` from 2 to 3.
- Bump `actions/github-script` from 8 to 9.
- Bump `codecov/codecov-action` from 5 to 6.
- Update opensomeip C++ submodule to v0.0.5.

## [0.1.3](https://github.com/vtz/opensomeip-python/releases/tag/v0.1.3) - 2026-03-30

### Miscellaneous

- Update opensomeip C++ submodule to v0.0.4.

## [0.1.2](https://github.com/vtz/opensomeip-python/releases/tag/v0.1.2) - 2026-03-15

### Bug Fixes

- Disable C++ extension in unit tests to prevent native transport `start()`
  from blocking on Windows during cibuildwheel test runs. Unit tests now always
  exercise the pure-Python path via an autouse conftest fixture.
- Trigger wheel builds on tag push instead of release event, fixing wheels not
  being built on new releases.

### Miscellaneous

- Bump `actions/checkout` from 4 to 6.

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
