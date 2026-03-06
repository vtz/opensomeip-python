#include <pybind11/pybind11.h>

namespace py = pybind11;

void init_serialization(py::module_& m) {
    // Serializer and Deserializer bindings will be added here
    // once opensomeip headers are available via the git submodule.
    //
    // Planned bindings:
    //   - py::class_<Serializer>
    //     .def("serialize_uint8", ...), serialize_uint16, ..., serialize_string
    //     .def("to_bytes", ... returning py::bytes)
    //   - py::class_<Deserializer>
    //     .def(py::init from py::bytes)
    //     .def("deserialize_uint8", ...), etc.
    //   - GIL released for large payload operations
}
