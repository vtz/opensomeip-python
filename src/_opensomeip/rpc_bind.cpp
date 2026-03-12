#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>
#include <pybind11/functional.h>

#include "rpc/rpc_types.h"
#include "rpc/rpc_client.h"
#include "rpc/rpc_server.h"

namespace py = pybind11;
using namespace someip::rpc;

void init_rpc(py::module_& m) {
    auto rpc = m.def_submodule("rpc", "RPC bindings");

    py::enum_<RpcResult>(rpc, "RpcResult")
        .value("SUCCESS", RpcResult::SUCCESS)
        .value("TIMEOUT", RpcResult::TIMEOUT)
        .value("NETWORK_ERROR", RpcResult::NETWORK_ERROR)
        .value("INVALID_PARAMETERS", RpcResult::INVALID_PARAMETERS)
        .value("METHOD_NOT_FOUND", RpcResult::METHOD_NOT_FOUND)
        .value("SERVICE_NOT_AVAILABLE", RpcResult::SERVICE_NOT_AVAILABLE)
        .value("INTERNAL_ERROR", RpcResult::INTERNAL_ERROR);

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
        .def(py::init<uint16_t>(), py::arg("client_id"))
        .def("initialize", &RpcClient::initialize)
        .def("shutdown", &RpcClient::shutdown, py::call_guard<py::gil_scoped_release>())
        .def("call_method_sync", &RpcClient::call_method_sync,
             py::arg("service_id"), py::arg("method_id"),
             py::arg("parameters"), py::arg("timeout") = RpcTimeout(),
             py::call_guard<py::gil_scoped_release>())
        .def("call_method_async", &RpcClient::call_method_async,
             py::arg("service_id"), py::arg("method_id"),
             py::arg("parameters"), py::arg("callback"),
             py::arg("timeout") = RpcTimeout(),
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
        .def(py::init<uint16_t>(), py::arg("service_id"))
        .def("initialize", &RpcServer::initialize)
        .def("shutdown", &RpcServer::shutdown, py::call_guard<py::gil_scoped_release>())
        .def("register_method", &RpcServer::register_method,
             py::arg("method_id"), py::arg("handler"))
        .def("unregister_method", &RpcServer::unregister_method, py::arg("method_id"))
        .def("is_method_registered", &RpcServer::is_method_registered, py::arg("method_id"))
        .def("get_registered_methods", &RpcServer::get_registered_methods)
        .def("is_ready", &RpcServer::is_ready)
        .def("get_statistics", &RpcServer::get_statistics);
}
