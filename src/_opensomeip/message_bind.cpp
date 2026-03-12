#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "someip/message.h"

namespace py = pybind11;
using namespace someip;

void init_message(py::module_& m) {
    py::class_<Message, std::shared_ptr<Message>>(m, "Message")
        .def(py::init<>())
        .def(py::init<MessageId, RequestId, MessageType, ReturnCode>(),
             py::arg("message_id"),
             py::arg("request_id"),
             py::arg("message_type") = MessageType::REQUEST,
             py::arg("return_code") = ReturnCode::E_OK)

        // Header field properties
        .def_property("message_id", &Message::get_message_id, &Message::set_message_id)
        .def_property("request_id", &Message::get_request_id, &Message::set_request_id)
        .def_property("message_type", &Message::get_message_type, &Message::set_message_type)
        .def_property("return_code", &Message::get_return_code, &Message::set_return_code)
        .def_property("protocol_version", &Message::get_protocol_version, &Message::set_protocol_version)
        .def_property("interface_version", &Message::get_interface_version, &Message::set_interface_version)
        .def_property("length", &Message::get_length, &Message::set_length)

        // Convenience ID accessors
        .def_property("service_id", &Message::get_service_id, &Message::set_service_id)
        .def_property("method_id", &Message::get_method_id, &Message::set_method_id)
        .def_property("client_id", &Message::get_client_id, &Message::set_client_id)
        .def_property("session_id", &Message::get_session_id, &Message::set_session_id)

        // Payload as py::bytes (copy from vector<uint8_t>)
        .def_property("payload",
            [](const Message& msg) -> py::bytes {
                auto& p = msg.get_payload();
                return py::bytes(reinterpret_cast<const char*>(p.data()), p.size());
            },
            [](Message& msg, py::bytes data) {
                auto sv = static_cast<std::string_view>(data);
                std::vector<uint8_t> vec(sv.begin(), sv.end());
                msg.set_payload(std::move(vec));
            })

        // Serialization
        .def("serialize", [](const Message& msg) -> py::bytes {
            auto data = msg.serialize();
            return py::bytes(reinterpret_cast<const char*>(data.data()), data.size());
        })
        .def("deserialize", [](Message& msg, py::bytes data) {
            auto sv = static_cast<std::string_view>(data);
            std::vector<uint8_t> vec(sv.begin(), sv.end());
            return msg.deserialize(vec);
        }, py::arg("data"))

        // Validation
        .def("is_valid", &Message::is_valid)
        .def("has_valid_header", &Message::has_valid_header)
        .def("has_valid_payload", &Message::has_valid_payload)
        .def("has_valid_message_id", &Message::has_valid_message_id)
        .def("has_valid_service_id", &Message::has_valid_service_id)
        .def("has_valid_method_id", &Message::has_valid_method_id)
        .def("has_valid_request_id", &Message::has_valid_request_id)
        .def("has_valid_client_id", &Message::has_valid_client_id)
        .def("has_valid_session_id", &Message::has_valid_session_id)
        .def("has_valid_length", &Message::has_valid_length)
        .def("has_valid_message_type", &Message::has_valid_message_type)
        .def("has_tp_flag", &Message::has_tp_flag)

        // Utility
        .def("get_total_size", &Message::get_total_size)
        .def_static("get_header_size", &Message::get_header_size)
        .def("is_request", &Message::is_request)
        .def("is_response", &Message::is_response)
        .def("uses_tp", &Message::uses_tp)
        .def("is_success", &Message::is_success)

        // E2E support
        .def("has_e2e_header", &Message::has_e2e_header)
        .def("get_e2e_header", &Message::get_e2e_header)
        .def("set_e2e_header", &Message::set_e2e_header, py::arg("header"))
        .def("clear_e2e_header", &Message::clear_e2e_header)

        .def("__repr__", &Message::to_string)
        .def("__eq__", [](const Message& a, const Message& b) {
            return a.get_message_id() == b.get_message_id()
                && a.get_request_id() == b.get_request_id()
                && a.get_message_type() == b.get_message_type()
                && a.get_return_code() == b.get_return_code()
                && a.get_protocol_version() == b.get_protocol_version()
                && a.get_interface_version() == b.get_interface_version()
                && a.get_payload() == b.get_payload();
        });

    // E2EHeader binding (needed for Message's E2E accessors)
    py::class_<e2e::E2EHeader>(m, "E2EHeader")
        .def(py::init<>())
        .def(py::init<uint32_t, uint32_t, uint16_t, uint16_t>(),
             py::arg("crc"), py::arg("counter"),
             py::arg("data_id"), py::arg("freshness_value"))
        .def_readwrite("crc", &e2e::E2EHeader::crc)
        .def_readwrite("counter", &e2e::E2EHeader::counter)
        .def_readwrite("data_id", &e2e::E2EHeader::data_id)
        .def_readwrite("freshness_value", &e2e::E2EHeader::freshness_value)
        .def("serialize", [](const e2e::E2EHeader& h) -> py::bytes {
            auto data = h.serialize();
            return py::bytes(reinterpret_cast<const char*>(data.data()), data.size());
        })
        .def("is_valid", &e2e::E2EHeader::is_valid)
        .def_static("get_header_size", &e2e::E2EHeader::get_header_size);
}
