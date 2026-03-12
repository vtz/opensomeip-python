#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>

#include "transport/endpoint.h"
#include "transport/transport.h"
#include "transport/udp_transport.h"
#include "transport/tcp_transport.h"

namespace py = pybind11;
using namespace someip;
using namespace someip::transport;

struct PyTransportListener : ITransportListener {
    using ITransportListener::ITransportListener;

    void on_message_received(MessagePtr message, const Endpoint& sender) override {
        py::gil_scoped_acquire gil;
        PYBIND11_OVERRIDE_PURE(void, ITransportListener, on_message_received, message, sender);
    }

    void on_connection_lost(const Endpoint& endpoint) override {
        py::gil_scoped_acquire gil;
        PYBIND11_OVERRIDE_PURE(void, ITransportListener, on_connection_lost, endpoint);
    }

    void on_connection_established(const Endpoint& endpoint) override {
        py::gil_scoped_acquire gil;
        PYBIND11_OVERRIDE_PURE(void, ITransportListener, on_connection_established, endpoint);
    }

    void on_error(Result error) override {
        py::gil_scoped_acquire gil;
        PYBIND11_OVERRIDE_PURE(void, ITransportListener, on_error, error);
    }
};

void init_transport(py::module_& m) {
    py::enum_<TransportProtocol>(m, "TransportProtocol")
        .value("UDP", TransportProtocol::UDP)
        .value("TCP", TransportProtocol::TCP)
        .value("MULTICAST_UDP", TransportProtocol::MULTICAST_UDP);

    py::class_<Endpoint>(m, "Endpoint")
        .def(py::init<>())
        .def(py::init<const std::string&, uint16_t, TransportProtocol>(),
             py::arg("address"), py::arg("port"),
             py::arg("protocol") = TransportProtocol::UDP)
        .def_property("address", &Endpoint::get_address, &Endpoint::set_address)
        .def_property("port", &Endpoint::get_port, &Endpoint::set_port)
        .def_property("protocol", &Endpoint::get_protocol, &Endpoint::set_protocol)
        .def("is_valid", &Endpoint::is_valid)
        .def("is_multicast", &Endpoint::is_multicast)
        .def("is_ipv4", &Endpoint::is_ipv4)
        .def("is_ipv6", &Endpoint::is_ipv6)
        .def("__repr__", &Endpoint::to_string)
        .def("__eq__", &Endpoint::operator==)
        .def("__ne__", &Endpoint::operator!=)
        .def("__lt__", &Endpoint::operator<)
        .def("__hash__", [](const Endpoint& e) { return Endpoint::Hash{}(e); });

    py::enum_<TcpConnectionState>(m, "TcpConnectionState")
        .value("DISCONNECTED", TcpConnectionState::DISCONNECTED)
        .value("CONNECTING", TcpConnectionState::CONNECTING)
        .value("CONNECTED", TcpConnectionState::CONNECTED)
        .value("DISCONNECTING", TcpConnectionState::DISCONNECTING);

    py::class_<ITransportListener, PyTransportListener>(m, "ITransportListener")
        .def(py::init<>())
        .def("on_message_received", &ITransportListener::on_message_received)
        .def("on_connection_lost", &ITransportListener::on_connection_lost)
        .def("on_connection_established", &ITransportListener::on_connection_established)
        .def("on_error", &ITransportListener::on_error);

    py::class_<UdpTransportConfig>(m, "UdpTransportConfig")
        .def(py::init<>())
        .def_readwrite("blocking", &UdpTransportConfig::blocking)
        .def_readwrite("receive_buffer_size", &UdpTransportConfig::receive_buffer_size)
        .def_readwrite("send_buffer_size", &UdpTransportConfig::send_buffer_size)
        .def_readwrite("reuse_address", &UdpTransportConfig::reuse_address)
        .def_readwrite("reuse_port", &UdpTransportConfig::reuse_port)
        .def_readwrite("enable_broadcast", &UdpTransportConfig::enable_broadcast)
        .def_readwrite("multicast_interface", &UdpTransportConfig::multicast_interface)
        .def_readwrite("multicast_ttl", &UdpTransportConfig::multicast_ttl)
        .def_readwrite("max_message_size", &UdpTransportConfig::max_message_size);

    py::class_<UdpTransport>(m, "UdpTransport")
        .def(py::init<const Endpoint&, const UdpTransportConfig&>(),
             py::arg("local_endpoint"),
             py::arg("config") = UdpTransportConfig())
        .def("start", &UdpTransport::start, py::call_guard<py::gil_scoped_release>())
        .def("stop", &UdpTransport::stop, py::call_guard<py::gil_scoped_release>())
        .def("send_message", &UdpTransport::send_message,
             py::arg("message"), py::arg("endpoint"),
             py::call_guard<py::gil_scoped_release>())
        .def("receive_message", &UdpTransport::receive_message)
        .def("is_running", &UdpTransport::is_running)
        .def("is_connected", &UdpTransport::is_connected)
        .def("get_local_endpoint", &UdpTransport::get_local_endpoint)
        .def("set_listener", &UdpTransport::set_listener, py::arg("listener"),
             py::keep_alive<1, 2>())
        .def("join_multicast_group", &UdpTransport::join_multicast_group,
             py::arg("multicast_address"),
             py::call_guard<py::gil_scoped_release>())
        .def("leave_multicast_group", &UdpTransport::leave_multicast_group,
             py::arg("multicast_address"),
             py::call_guard<py::gil_scoped_release>());

    py::class_<TcpTransportConfig>(m, "TcpTransportConfig")
        .def(py::init<>())
        .def_readwrite("connection_timeout", &TcpTransportConfig::connection_timeout)
        .def_readwrite("receive_timeout", &TcpTransportConfig::receive_timeout)
        .def_readwrite("send_timeout", &TcpTransportConfig::send_timeout)
        .def_readwrite("max_receive_buffer", &TcpTransportConfig::max_receive_buffer)
        .def_readwrite("max_connections", &TcpTransportConfig::max_connections)
        .def_readwrite("keep_alive", &TcpTransportConfig::keep_alive)
        .def_readwrite("keep_alive_interval", &TcpTransportConfig::keep_alive_interval);

    py::class_<TcpTransport>(m, "TcpTransport")
        .def(py::init<const TcpTransportConfig&>(),
             py::arg("config") = TcpTransportConfig())
        .def("initialize", &TcpTransport::initialize, py::arg("local_endpoint"),
             py::call_guard<py::gil_scoped_release>())
        .def("start", &TcpTransport::start, py::call_guard<py::gil_scoped_release>())
        .def("stop", &TcpTransport::stop, py::call_guard<py::gil_scoped_release>())
        .def("connect", &TcpTransport::connect, py::arg("endpoint"),
             py::call_guard<py::gil_scoped_release>())
        .def("disconnect", &TcpTransport::disconnect,
             py::call_guard<py::gil_scoped_release>())
        .def("send_message", &TcpTransport::send_message,
             py::arg("message"), py::arg("endpoint"),
             py::call_guard<py::gil_scoped_release>())
        .def("receive_message", &TcpTransport::receive_message)
        .def("is_running", &TcpTransport::is_running)
        .def("is_connected", &TcpTransport::is_connected)
        .def("get_local_endpoint", &TcpTransport::get_local_endpoint)
        .def("get_connection_state", &TcpTransport::get_connection_state)
        .def("set_listener", &TcpTransport::set_listener, py::arg("listener"),
             py::keep_alive<1, 2>())
        .def("enable_server_mode", &TcpTransport::enable_server_mode,
             py::arg("backlog") = 5,
             py::call_guard<py::gil_scoped_release>())
        .def("accept_connection", &TcpTransport::accept_connection,
             py::call_guard<py::gil_scoped_release>());
}
