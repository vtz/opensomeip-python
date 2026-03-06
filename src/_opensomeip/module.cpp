#include <pybind11/pybind11.h>

namespace py = pybind11;

// Forward declarations for sub-module init functions
void init_types(py::module_& m);
void init_message(py::module_& m);
void init_serialization(py::module_& m);
void init_transport(py::module_& m);
void init_sd(py::module_& m);
void init_rpc(py::module_& m);
void init_events(py::module_& m);
void init_tp(py::module_& m);
void init_e2e(py::module_& m);
void init_exceptions(py::module_& m);

PYBIND11_MODULE(_opensomeip, m) {
    m.doc() = "Python bindings for the opensomeip C++ SOME/IP stack";
    m.attr("__version__") = "0.1.0";

    init_exceptions(m);
    init_types(m);
    init_message(m);
    init_serialization(m);
    init_transport(m);
    init_sd(m);
    init_rpc(m);
    init_events(m);
    init_tp(m);
    init_e2e(m);
}
