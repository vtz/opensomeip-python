#include <pybind11/pybind11.h>

namespace py = pybind11;

void init_sd(py::module_& m) {
    // Service Discovery bindings will be added here once opensomeip
    // headers are available via the git submodule.
    //
    // Planned bindings:
    //   - py::class_<SdConfig>
    //   - py::class_<ServiceInstance>
    //   - py::class_<SdServer> with start/stop/offer/stop_offer (GIL released)
    //   - py::class_<SdClient> with start/stop/find/subscribe (GIL released,
    //     callbacks acquire GIL)
}
