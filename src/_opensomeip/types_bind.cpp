#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <sstream>

#include "someip/types.h"
#include "common/result.h"

namespace py = pybind11;
using namespace someip;

void init_types(py::module_& m) {
    py::enum_<MessageType>(m, "MessageType", py::arithmetic())
        .value("REQUEST", MessageType::REQUEST)
        .value("REQUEST_NO_RETURN", MessageType::REQUEST_NO_RETURN)
        .value("NOTIFICATION", MessageType::NOTIFICATION)
        .value("REQUEST_ACK", MessageType::REQUEST_ACK)
        .value("RESPONSE", MessageType::RESPONSE)
        .value("ERROR", MessageType::ERROR)
        .value("RESPONSE_ACK", MessageType::RESPONSE_ACK)
        .value("ERROR_ACK", MessageType::ERROR_ACK)
        .value("TP_REQUEST", MessageType::TP_REQUEST)
        .value("TP_REQUEST_NO_RETURN", MessageType::TP_REQUEST_NO_RETURN)
        .value("TP_NOTIFICATION", MessageType::TP_NOTIFICATION)
        .def("__str__", [](MessageType t) { return to_string(t); });

    py::enum_<ReturnCode>(m, "ReturnCode", py::arithmetic())
        .value("E_OK", ReturnCode::E_OK)
        .value("E_NOT_OK", ReturnCode::E_NOT_OK)
        .value("E_UNKNOWN_SERVICE", ReturnCode::E_UNKNOWN_SERVICE)
        .value("E_UNKNOWN_METHOD", ReturnCode::E_UNKNOWN_METHOD)
        .value("E_NOT_READY", ReturnCode::E_NOT_READY)
        .value("E_NOT_REACHABLE", ReturnCode::E_NOT_REACHABLE)
        .value("E_TIMEOUT", ReturnCode::E_TIMEOUT)
        .value("E_WRONG_PROTOCOL_VERSION", ReturnCode::E_WRONG_PROTOCOL_VERSION)
        .value("E_WRONG_INTERFACE_VERSION", ReturnCode::E_WRONG_INTERFACE_VERSION)
        .value("E_MALFORMED_MESSAGE", ReturnCode::E_MALFORMED_MESSAGE)
        .value("E_WRONG_MESSAGE_TYPE", ReturnCode::E_WRONG_MESSAGE_TYPE)
        .value("E_E2E_REPEATED", ReturnCode::E_E2E_REPEATED)
        .value("E_E2E_WRONG_SEQUENCE", ReturnCode::E_E2E_WRONG_SEQUENCE)
        .value("E_E2E", ReturnCode::E_E2E)
        .value("E_E2E_NOT_AVAILABLE", ReturnCode::E_E2E_NOT_AVAILABLE)
        .value("E_E2E_NO_NEW_DATA", ReturnCode::E_E2E_NO_NEW_DATA)
        .def("__str__", [](ReturnCode c) { return to_string(c); });

    py::enum_<Result>(m, "Result", py::arithmetic())
        .value("SUCCESS", Result::SUCCESS)
        .value("NETWORK_ERROR", Result::NETWORK_ERROR)
        .value("NOT_CONNECTED", Result::NOT_CONNECTED)
        .value("CONNECTION_LOST", Result::CONNECTION_LOST)
        .value("CONNECTION_REFUSED", Result::CONNECTION_REFUSED)
        .value("TIMEOUT", Result::TIMEOUT)
        .value("INVALID_ENDPOINT", Result::INVALID_ENDPOINT)
        .value("INVALID_MESSAGE", Result::INVALID_MESSAGE)
        .value("INVALID_MESSAGE_TYPE", Result::INVALID_MESSAGE_TYPE)
        .value("INVALID_SERVICE_ID", Result::INVALID_SERVICE_ID)
        .value("INVALID_METHOD_ID", Result::INVALID_METHOD_ID)
        .value("INVALID_PROTOCOL_VERSION", Result::INVALID_PROTOCOL_VERSION)
        .value("INVALID_INTERFACE_VERSION", Result::INVALID_INTERFACE_VERSION)
        .value("MALFORMED_MESSAGE", Result::MALFORMED_MESSAGE)
        .value("INVALID_SESSION_ID", Result::INVALID_SESSION_ID)
        .value("SESSION_EXPIRED", Result::SESSION_EXPIRED)
        .value("SESSION_NOT_FOUND", Result::SESSION_NOT_FOUND)
        .value("OUT_OF_MEMORY", Result::OUT_OF_MEMORY)
        .value("BUFFER_OVERFLOW", Result::BUFFER_OVERFLOW)
        .value("RESOURCE_EXHAUSTED", Result::RESOURCE_EXHAUSTED)
        .value("SERVICE_NOT_FOUND", Result::SERVICE_NOT_FOUND)
        .value("SERVICE_UNAVAILABLE", Result::SERVICE_UNAVAILABLE)
        .value("SUBSCRIPTION_FAILED", Result::SUBSCRIPTION_FAILED)
        .value("SAFETY_VIOLATION", Result::SAFETY_VIOLATION)
        .value("FAULT_DETECTED", Result::FAULT_DETECTED)
        .value("RECOVERY_FAILED", Result::RECOVERY_FAILED)
        .value("NOT_IMPLEMENTED", Result::NOT_IMPLEMENTED)
        .value("INVALID_ARGUMENT", Result::INVALID_ARGUMENT)
        .value("PERMISSION_DENIED", Result::PERMISSION_DENIED)
        .value("INTERNAL_ERROR", Result::INTERNAL_ERROR)
        .value("NOT_INITIALIZED", Result::NOT_INITIALIZED)
        .value("INVALID_STATE", Result::INVALID_STATE)
        .value("UNKNOWN_ERROR", Result::UNKNOWN_ERROR)
        .def("__str__", [](Result r) { return to_string(r); })
        .def("__bool__", [](Result r) { return is_success(r); });

    py::class_<MessageId>(m, "MessageId")
        .def(py::init<>())
        .def(py::init<uint16_t, uint16_t>(), py::arg("service_id"), py::arg("method_id"))
        .def_readwrite("service_id", &MessageId::service_id)
        .def_readwrite("method_id", &MessageId::method_id)
        .def("to_uint32", &MessageId::to_uint32)
        .def_static("from_uint32", &MessageId::from_uint32, py::arg("value"))
        .def("__eq__", &MessageId::operator==)
        .def("__ne__", &MessageId::operator!=)
        .def("__hash__", [](const MessageId& id) { return std::hash<uint32_t>{}(id.to_uint32()); })
        .def("__repr__", [](const MessageId& id) {
            std::ostringstream os;
            os << "MessageId(service_id=0x" << std::hex << id.service_id
               << ", method_id=0x" << id.method_id << ")";
            return os.str();
        });

    py::class_<RequestId>(m, "RequestId")
        .def(py::init<>())
        .def(py::init<uint16_t, uint16_t>(), py::arg("client_id"), py::arg("session_id"))
        .def_readwrite("client_id", &RequestId::client_id)
        .def_readwrite("session_id", &RequestId::session_id)
        .def("to_uint32", &RequestId::to_uint32)
        .def_static("from_uint32", &RequestId::from_uint32, py::arg("value"))
        .def("__eq__", &RequestId::operator==)
        .def("__ne__", &RequestId::operator!=)
        .def("__hash__", [](const RequestId& id) { return std::hash<uint32_t>{}(id.to_uint32()); })
        .def("__repr__", [](const RequestId& id) {
            std::ostringstream os;
            os << "RequestId(client_id=0x" << std::hex << id.client_id
               << ", session_id=0x" << id.session_id << ")";
            return os.str();
        });

    // Protocol constants
    m.attr("SOMEIP_PROTOCOL_VERSION") = SOMEIP_PROTOCOL_VERSION;
    m.attr("SOMEIP_INTERFACE_VERSION") = SOMEIP_INTERFACE_VERSION;
    m.attr("SOMEIP_SD_SERVICE_ID") = SOMEIP_SD_SERVICE_ID;
    m.attr("SOMEIP_SD_METHOD_ID") = SOMEIP_SD_METHOD_ID;
    m.attr("SOMEIP_SD_CLIENT_ID") = SOMEIP_SD_CLIENT_ID;

    // Free functions
    m.def("is_request", py::overload_cast<MessageType>(&is_request), py::arg("type"));
    m.def("is_response", py::overload_cast<MessageType>(&is_response), py::arg("type"));
    m.def("uses_tp", py::overload_cast<MessageType>(&uses_tp), py::arg("type"));
    m.def("get_ack_type", &get_ack_type, py::arg("type"));
    m.def("is_success", py::overload_cast<ReturnCode>(&is_success), py::arg("code"));
}
