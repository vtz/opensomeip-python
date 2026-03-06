Compatibility Matrix
====================

Python Versions
---------------

.. list-table::
   :header-rows: 1

   * - Python Version
     - Status
   * - 3.10
     - Supported
   * - 3.11
     - Supported
   * - 3.12
     - Supported
   * - 3.13
     - Supported
   * - 3.14+
     - Best-effort

Platforms
---------

.. list-table::
   :header-rows: 1

   * - Platform
     - Architecture
     - Status
   * - Linux
     - x86_64
     - Supported (CI)
   * - Linux
     - aarch64
     - Supported (CI via QEMU)
   * - macOS
     - x86_64
     - Supported (CI)
   * - macOS
     - arm64
     - Supported (CI)
   * - Windows
     - x86_64
     - Supported (CI)

opensomeip C++ Library
-----------------------

The ``opensomeip-python`` version tracks the pinned opensomeip C++ library
via a git submodule. The compatible version is recorded in ``pyproject.toml``
under ``[tool.opensomeip].opensomeip-version``.

.. list-table::
   :header-rows: 1

   * - opensomeip-python
     - opensomeip C++
   * - 0.1.x
     - 0.1.x (initial)

Nightly builds against the opensomeip ``main`` branch run via CI to
detect upstream breaking changes early.

ABI Stability
-------------

The compiled pybind11 extension (``_opensomeip``) is tied to a specific
Python minor version and platform. Wheels are built per Python version
via ``cibuildwheel``.

The public Python API (``opensomeip`` package) follows SemVer:

- **Major** version bump: breaking Python API changes
- **Minor** version bump: new features, new opensomeip APIs exposed
- **Patch** version bump: bug fixes only
