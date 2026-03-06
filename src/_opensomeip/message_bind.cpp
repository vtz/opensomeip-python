#include <pybind11/pybind11.h>

namespace py = pybind11;

void init_message(py::module_& m) {
    // Message class with shared_ptr<Message> holder will be bound here
    // once opensomeip headers are available via the git submodule.
    //
    // Planned bindings:
    //   - py::class_<Message, std::shared_ptr<Message>>
    //     .def(py::init<>())
    //     .def_property("message_id", ...)
    //     .def_property("request_id", ...)
    //     .def_property("message_type", ...)
    //     .def_property("return_code", ...)
    //     .def_property("payload", getter returning py::bytes, setter from bytes)
    //     .def("__repr__", ...)
    //     .def("__eq__", ...)
}
