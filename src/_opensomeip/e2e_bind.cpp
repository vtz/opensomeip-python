#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "e2e/e2e_config.h"
#include "e2e/e2e_header.h"
#include "e2e/e2e_profile.h"
#include "e2e/e2e_profile_registry.h"
#include "e2e/e2e_protection.h"
#include "e2e/e2e_crc.h"

namespace py = pybind11;
using namespace someip;
using namespace someip::e2e;

struct PyE2EProfile : E2EProfile {
    using E2EProfile::E2EProfile;

    Result protect(Message& msg, const E2EConfig& config) override {
        PYBIND11_OVERRIDE_PURE(Result, E2EProfile, protect, msg, config);
    }

    Result validate(const Message& msg, const E2EConfig& config) override {
        PYBIND11_OVERRIDE_PURE(Result, E2EProfile, validate, msg, config);
    }

    size_t get_header_size() const override {
        PYBIND11_OVERRIDE_PURE(size_t, E2EProfile, get_header_size);
    }

    std::string get_profile_name() const override {
        PYBIND11_OVERRIDE_PURE(std::string, E2EProfile, get_profile_name);
    }

    uint32_t get_profile_id() const override {
        PYBIND11_OVERRIDE_PURE(uint32_t, E2EProfile, get_profile_id);
    }
};

void init_e2e(py::module_& m) {
    auto e2e = m.def_submodule("e2e", "E2E protection bindings");

    py::class_<E2EConfig>(e2e, "E2EConfig")
        .def(py::init<>())
        .def(py::init<uint16_t>(), py::arg("data_id"))
        .def_readwrite("profile_id", &E2EConfig::profile_id)
        .def_readwrite("profile_name", &E2EConfig::profile_name)
        .def_readwrite("data_id", &E2EConfig::data_id)
        .def_readwrite("offset", &E2EConfig::offset)
        .def_readwrite("enable_crc", &E2EConfig::enable_crc)
        .def_readwrite("enable_counter", &E2EConfig::enable_counter)
        .def_readwrite("enable_freshness", &E2EConfig::enable_freshness)
        .def_readwrite("max_counter_value", &E2EConfig::max_counter_value)
        .def_readwrite("freshness_timeout_ms", &E2EConfig::freshness_timeout_ms)
        .def_readwrite("crc_type", &E2EConfig::crc_type);

    // E2EHeader is bound in message_bind.cpp, but also accessible here
    // via the e2e submodule for convenience
    e2e.attr("E2EHeader") = m.attr("E2EHeader");

    py::class_<E2EProfile, PyE2EProfile>(e2e, "E2EProfile")
        .def(py::init<>())
        .def("protect", &E2EProfile::protect, py::arg("message"), py::arg("config"))
        .def("validate", &E2EProfile::validate, py::arg("message"), py::arg("config"))
        .def("get_header_size", &E2EProfile::get_header_size)
        .def("get_profile_name", &E2EProfile::get_profile_name)
        .def("get_profile_id", &E2EProfile::get_profile_id);

    py::class_<E2EProfileRegistry, std::unique_ptr<E2EProfileRegistry, py::nodelete>>(e2e, "E2EProfileRegistry")
        .def_static("instance", &E2EProfileRegistry::instance,
                    py::return_value_policy::reference)
        .def("get_profile", py::overload_cast<uint32_t>(&E2EProfileRegistry::get_profile),
             py::arg("profile_id"), py::return_value_policy::reference)
        .def("get_profile_by_name",
             py::overload_cast<const std::string&>(&E2EProfileRegistry::get_profile),
             py::arg("profile_name"), py::return_value_policy::reference)
        .def("unregister_profile", &E2EProfileRegistry::unregister_profile, py::arg("profile_id"))
        .def("is_registered", &E2EProfileRegistry::is_registered, py::arg("profile_id"))
        .def("get_default_profile", &E2EProfileRegistry::get_default_profile,
             py::return_value_policy::reference);

    py::class_<E2EProtection>(e2e, "E2EProtection")
        .def(py::init<>())
        .def("protect", &E2EProtection::protect,
             py::arg("message"), py::arg("config"))
        .def("validate", &E2EProtection::validate,
             py::arg("message"), py::arg("config"))
        .def("extract_header", &E2EProtection::extract_header, py::arg("message"))
        .def("has_e2e_protection", &E2EProtection::has_e2e_protection, py::arg("message"));

    // CRC utility functions
    e2e.def("calculate_crc8_sae_j1850", &E2ECRC::calculate_crc8_sae_j1850, py::arg("data"));
    e2e.def("calculate_crc16_itu_x25", &E2ECRC::calculate_crc16_itu_x25, py::arg("data"));
    e2e.def("calculate_crc32", &E2ECRC::calculate_crc32, py::arg("data"));
    e2e.def("calculate_crc", &E2ECRC::calculate_crc,
            py::arg("data"), py::arg("offset"), py::arg("length"), py::arg("crc_type"));
}
