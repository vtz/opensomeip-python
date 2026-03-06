#include <pybind11/pybind11.h>

namespace py = pybind11;

void init_transport(py::module_& m) {
    // Transport bindings and ITransportListener trampoline will be added
    // here once opensomeip headers are available via the git submodule.
    //
    // Planned bindings:
    //   - py::class_<Endpoint> with ip, port
    //   - PyTransportListener trampoline (GIL acquired in overrides)
    //   - py::class_<UdpTransport> with start/stop/send (GIL released)
    //   - py::class_<TcpTransport> with start/stop/send/connect (GIL released)
}
