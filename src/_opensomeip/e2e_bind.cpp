#include <pybind11/pybind11.h>

namespace py = pybind11;

void init_e2e(py::module_& m) {
    // E2E Protection bindings will be added here once opensomeip
    // headers are available via the git submodule.
    //
    // Planned bindings:
    //   - py::class_<E2EProtection>
    //   - py::class_<E2EConfig>
    //   - PyE2EProfile trampoline for user-defined profiles
    //   - py::class_<E2EProfileRegistry>
    //   - CRC utility functions
}
