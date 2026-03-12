#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "serialization/serializer.h"

namespace py = pybind11;
using namespace someip;
using namespace someip::serialization;

namespace {

template<typename T>
T unwrap(DeserializationResult<T>&& result) {
    if (result.is_error()) {
        throw std::runtime_error(
            "Deserialization failed: " + to_string(result.get_error()));
    }
    return result.move_value();
}

} // namespace

void init_serialization(py::module_& m) {
    py::class_<Serializer>(m, "Serializer")
        .def(py::init<>())
        .def("reset", &Serializer::reset)
        .def("serialize_bool", &Serializer::serialize_bool, py::arg("value"))
        .def("serialize_uint8", &Serializer::serialize_uint8, py::arg("value"))
        .def("serialize_uint16", &Serializer::serialize_uint16, py::arg("value"))
        .def("serialize_uint32", &Serializer::serialize_uint32, py::arg("value"))
        .def("serialize_uint64", &Serializer::serialize_uint64, py::arg("value"))
        .def("serialize_int8", &Serializer::serialize_int8, py::arg("value"))
        .def("serialize_int16", &Serializer::serialize_int16, py::arg("value"))
        .def("serialize_int32", &Serializer::serialize_int32, py::arg("value"))
        .def("serialize_int64", &Serializer::serialize_int64, py::arg("value"))
        .def("serialize_float", &Serializer::serialize_float, py::arg("value"))
        .def("serialize_double", &Serializer::serialize_double, py::arg("value"))
        .def("serialize_string", &Serializer::serialize_string, py::arg("value"))
        .def("get_buffer", [](const Serializer& s) -> py::bytes {
            auto& buf = s.get_buffer();
            return py::bytes(reinterpret_cast<const char*>(buf.data()), buf.size());
        })
        .def("get_size", &Serializer::get_size)
        .def("align_to", &Serializer::align_to, py::arg("alignment"))
        .def("add_padding", &Serializer::add_padding, py::arg("bytes"));

    py::class_<Deserializer>(m, "Deserializer")
        .def(py::init([](py::bytes data) {
            auto sv = static_cast<std::string_view>(data);
            std::vector<uint8_t> vec(sv.begin(), sv.end());
            return std::make_unique<Deserializer>(std::move(vec));
        }), py::arg("data"))
        .def("reset", &Deserializer::reset)
        .def("deserialize_bool", [](Deserializer& d) { return unwrap(d.deserialize_bool()); })
        .def("deserialize_uint8", [](Deserializer& d) { return unwrap(d.deserialize_uint8()); })
        .def("deserialize_uint16", [](Deserializer& d) { return unwrap(d.deserialize_uint16()); })
        .def("deserialize_uint32", [](Deserializer& d) { return unwrap(d.deserialize_uint32()); })
        .def("deserialize_uint64", [](Deserializer& d) { return unwrap(d.deserialize_uint64()); })
        .def("deserialize_int8", [](Deserializer& d) { return unwrap(d.deserialize_int8()); })
        .def("deserialize_int16", [](Deserializer& d) { return unwrap(d.deserialize_int16()); })
        .def("deserialize_int32", [](Deserializer& d) { return unwrap(d.deserialize_int32()); })
        .def("deserialize_int64", [](Deserializer& d) { return unwrap(d.deserialize_int64()); })
        .def("deserialize_float", [](Deserializer& d) { return unwrap(d.deserialize_float()); })
        .def("deserialize_double", [](Deserializer& d) { return unwrap(d.deserialize_double()); })
        .def("deserialize_string", [](Deserializer& d) { return unwrap(d.deserialize_string()); })
        .def("is_valid", &Deserializer::is_valid)
        .def("get_position", &Deserializer::get_position)
        .def("get_remaining", &Deserializer::get_remaining)
        .def("set_position", &Deserializer::set_position, py::arg("pos"))
        .def("skip", &Deserializer::skip, py::arg("bytes"))
        .def("align_to", &Deserializer::align_to, py::arg("alignment"));
}
