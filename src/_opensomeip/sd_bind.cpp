#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>
#include <pybind11/functional.h>

#include "sd/sd_types.h"
#include "sd/sd_client.h"
#include "sd/sd_server.h"

namespace py = pybind11;
using namespace someip::sd;

void init_sd(py::module_& m) {
    auto sd = m.def_submodule("sd", "Service Discovery bindings");

    py::enum_<EntryType>(sd, "EntryType")
        .value("FIND_SERVICE", EntryType::FIND_SERVICE)
        .value("OFFER_SERVICE", EntryType::OFFER_SERVICE)
        .value("REQUEST_SUBSCRIBE_EVENTGROUP", EntryType::REQUEST_SUBSCRIBE_EVENTGROUP)
        .value("SUBSCRIBE_EVENTGROUP_ACK", EntryType::SUBSCRIBE_EVENTGROUP_ACK);

    py::enum_<OptionType>(sd, "OptionType")
        .value("CONFIGURATION", OptionType::CONFIGURATION)
        .value("LOAD_BALANCING", OptionType::LOAD_BALANCING)
        .value("IPV4_ENDPOINT", OptionType::IPV4_ENDPOINT)
        .value("IPV6_ENDPOINT", OptionType::IPV6_ENDPOINT)
        .value("IPV4_MULTICAST", OptionType::IPV4_MULTICAST)
        .value("IPV6_MULTICAST", OptionType::IPV6_MULTICAST)
        .value("IPV4_SD_ENDPOINT", OptionType::IPV4_SD_ENDPOINT)
        .value("IPV6_SD_ENDPOINT", OptionType::IPV6_SD_ENDPOINT);

    py::enum_<SdResult>(sd, "SdResult")
        .value("SUCCESS", SdResult::SUCCESS)
        .value("SERVICE_NOT_FOUND", SdResult::SERVICE_NOT_FOUND)
        .value("SERVICE_ALREADY_EXISTS", SdResult::SERVICE_ALREADY_EXISTS)
        .value("NETWORK_ERROR", SdResult::NETWORK_ERROR)
        .value("TIMEOUT", SdResult::TIMEOUT)
        .value("INVALID_PARAMETERS", SdResult::INVALID_PARAMETERS);

    py::enum_<SubscriptionState>(sd, "SubscriptionState")
        .value("REQUESTED", SubscriptionState::REQUESTED)
        .value("SUBSCRIBED", SubscriptionState::SUBSCRIBED)
        .value("PENDING_ACK", SubscriptionState::PENDING_ACK)
        .value("REJECTED", SubscriptionState::REJECTED);

    py::class_<ServiceInstance>(sd, "ServiceInstance")
        .def(py::init<uint16_t, uint16_t, uint8_t, uint8_t>(),
             py::arg("service_id") = 0, py::arg("instance_id") = 0,
             py::arg("major_version") = 0, py::arg("minor_version") = 0)
        .def_readwrite("service_id", &ServiceInstance::service_id)
        .def_readwrite("instance_id", &ServiceInstance::instance_id)
        .def_readwrite("major_version", &ServiceInstance::major_version)
        .def_readwrite("minor_version", &ServiceInstance::minor_version)
        .def_readwrite("ip_address", &ServiceInstance::ip_address)
        .def_readwrite("port", &ServiceInstance::port)
        .def_readwrite("protocol", &ServiceInstance::protocol)
        .def_readwrite("ttl_seconds", &ServiceInstance::ttl_seconds);

    py::class_<EventGroup>(sd, "EventGroup")
        .def(py::init<uint16_t, uint8_t, uint8_t>(),
             py::arg("eventgroup_id") = 0,
             py::arg("major_version") = 0, py::arg("minor_version") = 0)
        .def_readwrite("eventgroup_id", &EventGroup::eventgroup_id)
        .def_readwrite("major_version", &EventGroup::major_version)
        .def_readwrite("minor_version", &EventGroup::minor_version)
        .def_readwrite("event_ids", &EventGroup::event_ids);

    py::class_<SdConfig>(sd, "SdConfig")
        .def(py::init<>())
        .def_readwrite("multicast_address", &SdConfig::multicast_address)
        .def_readwrite("multicast_port", &SdConfig::multicast_port)
        .def_readwrite("unicast_address", &SdConfig::unicast_address)
        .def_readwrite("unicast_port", &SdConfig::unicast_port)
        .def_readwrite("initial_delay", &SdConfig::initial_delay)
        .def_readwrite("repetition_base", &SdConfig::repetition_base)
        .def_readwrite("repetition_max", &SdConfig::repetition_max)
        .def_readwrite("repetition_multiplier", &SdConfig::repetition_multiplier)
        .def_readwrite("cyclic_offer", &SdConfig::cyclic_offer)
        .def_readwrite("ttl", &SdConfig::ttl)
        .def_readwrite("max_services", &SdConfig::max_services);

    py::class_<EventGroupSubscription>(sd, "EventGroupSubscription")
        .def(py::init<uint16_t, uint16_t, uint16_t>(),
             py::arg("service_id") = 0, py::arg("instance_id") = 0,
             py::arg("eventgroup_id") = 0)
        .def_readwrite("service_id", &EventGroupSubscription::service_id)
        .def_readwrite("instance_id", &EventGroupSubscription::instance_id)
        .def_readwrite("eventgroup_id", &EventGroupSubscription::eventgroup_id)
        .def_readwrite("state", &EventGroupSubscription::state);

    py::class_<SdClient> sd_client(sd, "SdClient");
    py::class_<SdClient::Statistics>(sd_client, "Statistics")
        .def(py::init<>())
        .def_readonly("find_requests_sent", &SdClient::Statistics::find_requests_sent)
        .def_readonly("services_found", &SdClient::Statistics::services_found)
        .def_readonly("services_lost", &SdClient::Statistics::services_lost)
        .def_readonly("subscriptions_active", &SdClient::Statistics::subscriptions_active)
        .def_readonly("eventgroup_subscriptions", &SdClient::Statistics::eventgroup_subscriptions);
    sd_client
        .def(py::init<const SdConfig&>(), py::arg("config") = SdConfig())
        .def("initialize", &SdClient::initialize)
        .def("shutdown", &SdClient::shutdown, py::call_guard<py::gil_scoped_release>())
        .def("find_service", &SdClient::find_service,
             py::arg("service_id"), py::arg("callback"),
             py::arg("timeout") = std::chrono::milliseconds(0),
             py::call_guard<py::gil_scoped_release>())
        .def("subscribe_service", &SdClient::subscribe_service,
             py::arg("service_id"), py::arg("available_callback"),
             py::arg("unavailable_callback"),
             py::call_guard<py::gil_scoped_release>())
        .def("unsubscribe_service", &SdClient::unsubscribe_service,
             py::arg("service_id"))
        .def("subscribe_eventgroup", &SdClient::subscribe_eventgroup,
             py::arg("service_id"), py::arg("instance_id"), py::arg("eventgroup_id"),
             py::call_guard<py::gil_scoped_release>())
        .def("unsubscribe_eventgroup", &SdClient::unsubscribe_eventgroup,
             py::arg("service_id"), py::arg("instance_id"), py::arg("eventgroup_id"))
        .def("get_available_services", &SdClient::get_available_services,
             py::arg("service_id") = 0)
        .def("is_ready", &SdClient::is_ready)
        .def("get_statistics", &SdClient::get_statistics);

    py::class_<SdServer> sd_server(sd, "SdServer");
    py::class_<SdServer::Statistics>(sd_server, "Statistics")
        .def(py::init<>())
        .def_readonly("services_offered", &SdServer::Statistics::services_offered)
        .def_readonly("find_requests_received", &SdServer::Statistics::find_requests_received)
        .def_readonly("offers_sent", &SdServer::Statistics::offers_sent)
        .def_readonly("subscriptions_received", &SdServer::Statistics::subscriptions_received)
        .def_readonly("subscriptions_acknowledged", &SdServer::Statistics::subscriptions_acknowledged);
    sd_server
        .def(py::init<const SdConfig&>(), py::arg("config") = SdConfig())
        .def("initialize", &SdServer::initialize)
        .def("shutdown", &SdServer::shutdown, py::call_guard<py::gil_scoped_release>())
        .def("offer_service", &SdServer::offer_service,
             py::arg("instance"), py::arg("unicast_endpoint"),
             py::arg("multicast_endpoint") = "",
             py::call_guard<py::gil_scoped_release>())
        .def("stop_offer_service", &SdServer::stop_offer_service,
             py::arg("service_id"), py::arg("instance_id"),
             py::call_guard<py::gil_scoped_release>())
        .def("update_service_ttl", &SdServer::update_service_ttl,
             py::arg("service_id"), py::arg("instance_id"), py::arg("ttl_seconds"))
        .def("handle_eventgroup_subscription", &SdServer::handle_eventgroup_subscription,
             py::arg("service_id"), py::arg("instance_id"), py::arg("eventgroup_id"),
             py::arg("client_address"), py::arg("acknowledge") = true)
        .def("get_offered_services", &SdServer::get_offered_services)
        .def("is_ready", &SdServer::is_ready)
        .def("get_statistics", &SdServer::get_statistics);
}
