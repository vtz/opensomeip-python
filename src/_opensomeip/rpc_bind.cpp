#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>
#include <pybind11/functional.h>

#include <memory>
#include <string_view>

#include "rpc/rpc_types.h"
#include "rpc/rpc_client.h"
#include "rpc/rpc_server.h"
#include "transport/service_demux.h"
#include "transport/transport.h"

namespace py = pybind11;
using namespace someip::rpc;

namespace {

// Native request handling copies the callback without the GIL. Copying this
// handle does not touch Python; the last owner releases it with the GIL held.
struct PyMethodHandler {
    py::function fn;

    explicit PyMethodHandler(py::function callback) : fn(std::move(callback)) {}

    PyMethodHandler(const PyMethodHandler&) = delete;
    PyMethodHandler& operator=(const PyMethodHandler&) = delete;

    ~PyMethodHandler() {
        if (fn && Py_IsInitialized() != 0) {
            py::gil_scoped_acquire gil;
            fn = py::function();
        }
    }
};

bool register_python_method(RpcServer& server, MethodId method_id, py::function handler,
                            MethodSemantics semantics) {
    auto holder = std::make_shared<PyMethodHandler>(std::move(handler));
    return server.register_method(
        method_id,
        [holder](uint16_t client_id, uint16_t session_id,
                 const someip::platform::ByteBuffer& input,
                 someip::platform::ByteBuffer& output) {
            py::gil_scoped_acquire gil;
            try {
                const py::bytes payload =
                    input.empty() ? py::bytes()
                                  : py::bytes(reinterpret_cast<const char*>(input.data()),
                                              input.size());
                py::object result = holder->fn(client_id, session_id, payload);
                if (py::isinstance<py::tuple>(result)) {
                    const auto items = result.cast<py::tuple>();
                    if (items.size() != 2U) {
                        return RpcResult::INTERNAL_ERROR;
                    }
                    const auto code = items[0].cast<RpcResult>();
                    const auto body = items[1].cast<py::bytes>();
                    const auto view = static_cast<std::string_view>(body);
                    output.assign(view.begin(), view.end());
                    return code;
                }
                return result.cast<RpcResult>();
            } catch (const py::error_already_set&) {
                return RpcResult::INTERNAL_ERROR;
            } catch (const py::cast_error&) {
                return RpcResult::INTERNAL_ERROR;
            } catch (...) {
                return RpcResult::INTERNAL_ERROR;
            }
        },
        semantics);
}

}  // namespace

void init_rpc(py::module_& m) {
    auto rpc = m.def_submodule("rpc", "RPC bindings");

    py::enum_<RpcResult>(rpc, "RpcResult")
        .value("SUCCESS", RpcResult::SUCCESS)
        .value("TIMEOUT", RpcResult::TIMEOUT)
        .value("NETWORK_ERROR", RpcResult::NETWORK_ERROR)
        .value("INVALID_PARAMETERS", RpcResult::INVALID_PARAMETERS)
        .value("METHOD_NOT_FOUND", RpcResult::METHOD_NOT_FOUND)
        .value("SERVICE_NOT_AVAILABLE", RpcResult::SERVICE_NOT_AVAILABLE)
        .value("WRONG_INTERFACE_VERSION", RpcResult::WRONG_INTERFACE_VERSION)
        .value("INTERNAL_ERROR", RpcResult::INTERNAL_ERROR);

    py::enum_<MethodSemantics>(rpc, "MethodSemantics")
        .value("REQUEST_RESPONSE", MethodSemantics::REQUEST_RESPONSE)
        .value("FIRE_AND_FORGET", MethodSemantics::FIRE_AND_FORGET);

    py::class_<RpcTimeout>(rpc, "RpcTimeout")
        .def(py::init<>())
        .def_readwrite("request_timeout", &RpcTimeout::request_timeout)
        .def_readwrite("response_timeout", &RpcTimeout::response_timeout);

    py::class_<RpcRequest>(rpc, "RpcRequest")
        .def(py::init<uint16_t, uint16_t, uint16_t, uint16_t>(),
             py::arg("service_id") = 0, py::arg("method_id") = 0,
             py::arg("client_id") = 0, py::arg("session_id") = 0)
        .def_readwrite("service_id", &RpcRequest::service_id)
        .def_readwrite("method_id", &RpcRequest::method_id)
        .def_readwrite("client_id", &RpcRequest::client_id)
        .def_readwrite("session_id", &RpcRequest::session_id)
        .def_readwrite("parameters", &RpcRequest::parameters)
        .def_readwrite("timeout", &RpcRequest::timeout);

    py::class_<RpcResponse>(rpc, "RpcResponse")
        .def(py::init<uint16_t, uint16_t, uint16_t, uint16_t, RpcResult>(),
             py::arg("service_id") = 0, py::arg("method_id") = 0,
             py::arg("client_id") = 0, py::arg("session_id") = 0,
             py::arg("result") = RpcResult::SUCCESS)
        .def_readwrite("service_id", &RpcResponse::service_id)
        .def_readwrite("method_id", &RpcResponse::method_id)
        .def_readwrite("client_id", &RpcResponse::client_id)
        .def_readwrite("session_id", &RpcResponse::session_id)
        .def_readwrite("result", &RpcResponse::result)
        .def_readwrite("return_values", &RpcResponse::return_values);

    py::class_<RpcSyncResult>(rpc, "RpcSyncResult")
        .def(py::init<>())
        .def_readwrite("result", &RpcSyncResult::result)
        .def_readwrite("return_values", &RpcSyncResult::return_values)
        .def_readwrite("response_time", &RpcSyncResult::response_time);

    py::class_<RpcClient> rpc_client(rpc, "RpcClient");
    py::class_<RpcClient::Statistics>(rpc_client, "Statistics")
        .def(py::init<>())
        .def_readonly("total_calls", &RpcClient::Statistics::total_calls)
        .def_readonly("successful_calls", &RpcClient::Statistics::successful_calls)
        .def_readonly("failed_calls", &RpcClient::Statistics::failed_calls)
        .def_readonly("timeout_calls", &RpcClient::Statistics::timeout_calls)
        .def_readonly("average_response_time", &RpcClient::Statistics::average_response_time);
    rpc_client
        .def(py::init<uint16_t, uint8_t, const someip::transport::Endpoint&>(),
             py::arg("client_id"),
             py::arg("interface_version") = static_cast<uint8_t>(0x01),
             py::arg("local_bind") = someip::transport::Endpoint("0.0.0.0", 0))
        .def(py::init<uint16_t, someip::transport::ITransport&, uint8_t>(),
             py::arg("client_id"), py::arg("transport"),
             py::arg("interface_version") = static_cast<uint8_t>(0x01),
             py::keep_alive<1, 3>())
        .def("initialize", &RpcClient::initialize)
        .def("shutdown", &RpcClient::shutdown, py::call_guard<py::gil_scoped_release>())
        .def("set_remote_endpoint", &RpcClient::set_remote_endpoint, py::arg("endpoint"))
        .def("get_local_endpoint", &RpcClient::get_local_endpoint)
        .def("get_transport_result", &RpcClient::get_transport_result)
        .def("session_count", &RpcClient::session_count)
        .def("call_method_sync",
             static_cast<RpcSyncResult (RpcClient::*)(
                 uint16_t, MethodId, const someip::platform::ByteBuffer&, const RpcTimeout&)>(
                 &RpcClient::call_method_sync),
             py::arg("service_id"), py::arg("method_id"),
             py::arg("parameters"), py::arg("timeout") = RpcTimeout(),
             py::call_guard<py::gil_scoped_release>())
        .def("call_method_sync",
             static_cast<RpcSyncResult (RpcClient::*)(
                 uint16_t, MethodId, const someip::platform::ByteBuffer&,
                 const someip::transport::Endpoint&, const RpcTimeout&)>(
                 &RpcClient::call_method_sync),
             py::arg("service_id"), py::arg("method_id"),
             py::arg("parameters"), py::arg("server_endpoint"),
             py::arg("timeout") = RpcTimeout(),
             py::call_guard<py::gil_scoped_release>())
        .def("call_method_async",
             static_cast<RpcCallHandle (RpcClient::*)(
                 uint16_t, MethodId, const someip::platform::ByteBuffer&, RpcCallback,
                 const RpcTimeout&)>(
                 &RpcClient::call_method_async),
             py::arg("service_id"), py::arg("method_id"),
             py::arg("parameters"), py::arg("callback"),
             py::arg("timeout") = RpcTimeout(),
             py::call_guard<py::gil_scoped_release>())
        .def("call_method_async",
             static_cast<RpcCallHandle (RpcClient::*)(
                 uint16_t, MethodId, const someip::platform::ByteBuffer&, RpcCallback,
                 const someip::transport::Endpoint&, const RpcTimeout&)>(
                 &RpcClient::call_method_async),
             py::arg("service_id"), py::arg("method_id"),
             py::arg("parameters"), py::arg("callback"),
             py::arg("server_endpoint"), py::arg("timeout") = RpcTimeout(),
             py::call_guard<py::gil_scoped_release>())
        .def("send_request_no_return", &RpcClient::send_request_no_return,
             py::arg("service_id"), py::arg("method_id"),
             py::arg("parameters"), py::arg("dest"),
             py::call_guard<py::gil_scoped_release>())
        .def("cancel_call", &RpcClient::cancel_call, py::arg("handle"))
        .def("is_ready", &RpcClient::is_ready)
        .def("get_statistics", &RpcClient::get_statistics);

    py::class_<RpcServer> rpc_server(rpc, "RpcServer");
    py::class_<RpcServer::Statistics>(rpc_server, "Statistics")
        .def(py::init<>())
        .def_readonly("total_calls_received", &RpcServer::Statistics::total_calls_received)
        .def_readonly("successful_calls", &RpcServer::Statistics::successful_calls)
        .def_readonly("failed_calls", &RpcServer::Statistics::failed_calls)
        .def_readonly("method_not_found_errors", &RpcServer::Statistics::method_not_found_errors)
        .def_readonly("average_processing_time", &RpcServer::Statistics::average_processing_time);
    rpc_server
        .def(py::init<uint16_t, uint8_t, const someip::transport::Endpoint&>(),
             py::arg("service_id"),
             py::arg("interface_version") = static_cast<uint8_t>(0x01),
             py::arg("bind_endpoint") = someip::transport::Endpoint(
                 "127.0.0.1", SOMEIP_DEFAULT_RPC_PORT))
        .def(py::init<uint16_t, someip::transport::ITransport&, uint8_t>(),
             py::arg("service_id"), py::arg("transport"),
             py::arg("interface_version") = static_cast<uint8_t>(0x01),
             py::keep_alive<1, 3>())
        .def(py::init<uint16_t, someip::transport::ServiceDemux&, uint8_t>(),
             py::arg("service_id"), py::arg("demux"),
             py::arg("interface_version") = static_cast<uint8_t>(0x01),
             py::keep_alive<1, 3>())
        .def("initialize", &RpcServer::initialize)
        .def("shutdown", &RpcServer::shutdown, py::call_guard<py::gil_scoped_release>())
        .def("register_method", &register_python_method,
             py::arg("method_id"), py::arg("handler"),
             py::arg("semantics") = MethodSemantics::REQUEST_RESPONSE)
        .def("get_local_endpoint", &RpcServer::get_local_endpoint)
        .def("get_transport_result", &RpcServer::get_transport_result)
        .def("unregister_method", &RpcServer::unregister_method, py::arg("method_id"))
        .def("is_method_registered", &RpcServer::is_method_registered, py::arg("method_id"))
        .def("get_registered_methods", &RpcServer::get_registered_methods)
        .def("is_ready", &RpcServer::is_ready)
        .def("get_statistics", &RpcServer::get_statistics);
}
