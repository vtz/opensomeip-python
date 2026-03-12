#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>
#include <pybind11/functional.h>

#include "events/event_types.h"
#include "events/event_publisher.h"
#include "events/event_subscriber.h"

namespace py = pybind11;
using namespace someip::events;

void init_events(py::module_& m) {
    auto events = m.def_submodule("events", "Events bindings");

    py::enum_<Reliability>(events, "Reliability")
        .value("UNKNOWN", Reliability::UNKNOWN)
        .value("UNRELIABLE", Reliability::UNRELIABLE)
        .value("RELIABLE", Reliability::RELIABLE);

    py::enum_<NotificationType>(events, "NotificationType")
        .value("UNKNOWN", NotificationType::UNKNOWN)
        .value("PERIODIC", NotificationType::PERIODIC)
        .value("ON_CHANGE", NotificationType::ON_CHANGE)
        .value("ON_CHANGE_WITH_FILTER", NotificationType::ON_CHANGE_WITH_FILTER)
        .value("POLLING", NotificationType::POLLING);

    py::enum_<EventResult>(events, "EventResult")
        .value("SUCCESS", EventResult::SUCCESS)
        .value("EVENT_NOT_FOUND", EventResult::EVENT_NOT_FOUND)
        .value("SUBSCRIPTION_FAILED", EventResult::SUBSCRIPTION_FAILED)
        .value("NETWORK_ERROR", EventResult::NETWORK_ERROR)
        .value("TIMEOUT", EventResult::TIMEOUT)
        .value("INVALID_PARAMETERS", EventResult::INVALID_PARAMETERS)
        .value("NOT_AUTHORIZED", EventResult::NOT_AUTHORIZED);

    py::enum_<SubscriptionState>(events, "SubscriptionState")
        .value("REQUESTED", SubscriptionState::REQUESTED)
        .value("SUBSCRIBED", SubscriptionState::SUBSCRIBED)
        .value("PENDING", SubscriptionState::PENDING)
        .value("REJECTED", SubscriptionState::REJECTED)
        .value("EXPIRED", SubscriptionState::EXPIRED);

    py::enum_<PublicationPolicy>(events, "PublicationPolicy")
        .value("IMMEDIATE", PublicationPolicy::IMMEDIATE)
        .value("CYCLIC", PublicationPolicy::CYCLIC)
        .value("ON_REQUEST", PublicationPolicy::ON_REQUEST)
        .value("TRIGGERED", PublicationPolicy::TRIGGERED);

    py::class_<EventSubscription>(events, "EventSubscription")
        .def(py::init<uint16_t, uint16_t, uint16_t, uint16_t>(),
             py::arg("service_id") = 0, py::arg("instance_id") = 0,
             py::arg("event_id") = 0, py::arg("eventgroup_id") = 0)
        .def_readwrite("service_id", &EventSubscription::service_id)
        .def_readwrite("instance_id", &EventSubscription::instance_id)
        .def_readwrite("event_id", &EventSubscription::event_id)
        .def_readwrite("eventgroup_id", &EventSubscription::eventgroup_id)
        .def_readwrite("state", &EventSubscription::state)
        .def_readwrite("reliability", &EventSubscription::reliability)
        .def_readwrite("notification_type", &EventSubscription::notification_type)
        .def_readwrite("cycle_time", &EventSubscription::cycle_time);

    py::class_<EventNotification>(events, "EventNotification")
        .def(py::init<uint16_t, uint16_t, uint16_t>(),
             py::arg("service_id") = 0, py::arg("instance_id") = 0,
             py::arg("event_id") = 0)
        .def_readwrite("service_id", &EventNotification::service_id)
        .def_readwrite("instance_id", &EventNotification::instance_id)
        .def_readwrite("event_id", &EventNotification::event_id)
        .def_readwrite("client_id", &EventNotification::client_id)
        .def_readwrite("session_id", &EventNotification::session_id)
        .def_readwrite("event_data", &EventNotification::event_data);

    py::class_<EventConfig>(events, "EventConfig")
        .def(py::init<>())
        .def_readwrite("event_id", &EventConfig::event_id)
        .def_readwrite("eventgroup_id", &EventConfig::eventgroup_id)
        .def_readwrite("reliability", &EventConfig::reliability)
        .def_readwrite("notification_type", &EventConfig::notification_type)
        .def_readwrite("cycle_time", &EventConfig::cycle_time)
        .def_readwrite("is_field", &EventConfig::is_field)
        .def_readwrite("event_name", &EventConfig::event_name);

    py::class_<EventFilter>(events, "EventFilter")
        .def(py::init<>())
        .def_readwrite("event_id", &EventFilter::event_id)
        .def_readwrite("filter_data", &EventFilter::filter_data)
        .def("__eq__", &EventFilter::operator==);

    py::class_<EventPublisher> pub(events, "EventPublisher");
    py::class_<EventPublisher::Statistics>(pub, "Statistics")
        .def(py::init<>())
        .def_readonly("events_registered", &EventPublisher::Statistics::events_registered)
        .def_readonly("notifications_sent", &EventPublisher::Statistics::notifications_sent)
        .def_readonly("subscriptions_active", &EventPublisher::Statistics::subscriptions_active)
        .def_readonly("subscriptions_rejected", &EventPublisher::Statistics::subscriptions_rejected)
        .def_readonly("average_publish_time", &EventPublisher::Statistics::average_publish_time);
    pub
        .def(py::init<uint16_t, uint16_t>(),
             py::arg("service_id"), py::arg("instance_id"))
        .def("initialize", &EventPublisher::initialize)
        .def("shutdown", &EventPublisher::shutdown, py::call_guard<py::gil_scoped_release>())
        .def("register_event", &EventPublisher::register_event, py::arg("config"))
        .def("unregister_event", &EventPublisher::unregister_event, py::arg("event_id"))
        .def("update_event_config", &EventPublisher::update_event_config,
             py::arg("event_id"), py::arg("config"))
        .def("publish_event", &EventPublisher::publish_event,
             py::arg("event_id"), py::arg("data"),
             py::call_guard<py::gil_scoped_release>())
        .def("publish_field", &EventPublisher::publish_field,
             py::arg("event_id"), py::arg("data"),
             py::call_guard<py::gil_scoped_release>())
        .def("handle_subscription", &EventPublisher::handle_subscription,
             py::arg("eventgroup_id"), py::arg("client_id"),
             py::arg("filters") = std::vector<EventFilter>{})
        .def("handle_unsubscription", &EventPublisher::handle_unsubscription,
             py::arg("eventgroup_id"), py::arg("client_id"))
        .def("get_registered_events", &EventPublisher::get_registered_events)
        .def("get_subscriptions", &EventPublisher::get_subscriptions,
             py::arg("eventgroup_id"))
        .def("is_ready", &EventPublisher::is_ready)
        .def("get_statistics", &EventPublisher::get_statistics);

    py::class_<EventSubscriber> sub(events, "EventSubscriber");
    py::class_<EventSubscriber::Statistics>(sub, "Statistics")
        .def(py::init<>())
        .def_readonly("subscriptions_active", &EventSubscriber::Statistics::subscriptions_active)
        .def_readonly("notifications_received", &EventSubscriber::Statistics::notifications_received)
        .def_readonly("subscription_requests_sent", &EventSubscriber::Statistics::subscription_requests_sent)
        .def_readonly("subscription_responses_received", &EventSubscriber::Statistics::subscription_responses_received)
        .def_readonly("average_response_time", &EventSubscriber::Statistics::average_response_time);
    sub
        .def(py::init<uint16_t>(), py::arg("client_id"))
        .def("initialize", &EventSubscriber::initialize)
        .def("shutdown", &EventSubscriber::shutdown, py::call_guard<py::gil_scoped_release>())
        .def("subscribe_eventgroup", &EventSubscriber::subscribe_eventgroup,
             py::arg("service_id"), py::arg("instance_id"), py::arg("eventgroup_id"),
             py::arg("notification_callback"),
             py::arg("status_callback") = nullptr,
             py::arg("filters") = std::vector<EventFilter>{},
             py::call_guard<py::gil_scoped_release>())
        .def("unsubscribe_eventgroup", &EventSubscriber::unsubscribe_eventgroup,
             py::arg("service_id"), py::arg("instance_id"), py::arg("eventgroup_id"))
        .def("request_field", &EventSubscriber::request_field,
             py::arg("service_id"), py::arg("instance_id"), py::arg("event_id"),
             py::arg("callback"),
             py::call_guard<py::gil_scoped_release>())
        .def("set_event_filters", &EventSubscriber::set_event_filters,
             py::arg("service_id"), py::arg("instance_id"), py::arg("eventgroup_id"),
             py::arg("filters"))
        .def("get_active_subscriptions", &EventSubscriber::get_active_subscriptions)
        .def("get_subscription_status", &EventSubscriber::get_subscription_status,
             py::arg("service_id"), py::arg("instance_id"), py::arg("eventgroup_id"))
        .def("is_ready", &EventSubscriber::is_ready)
        .def("get_statistics", &EventSubscriber::get_statistics);
}
