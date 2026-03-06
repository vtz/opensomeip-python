#include <pybind11/pybind11.h>

namespace py = pybind11;

void init_types(py::module_& m) {
    // Enums and value types will be bound here once opensomeip
    // headers are available via the git submodule.
    //
    // Planned bindings:
    //   - py::enum_<MessageType>
    //   - py::enum_<ReturnCode>
    //   - py::enum_<ProtocolVersion>
    //   - py::class_<MessageId> with service_id, method_id, __repr__, __eq__, __hash__
    //   - py::class_<RequestId> with client_id, session_id, __repr__, __eq__, __hash__
}
