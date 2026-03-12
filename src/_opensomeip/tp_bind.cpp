#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>
#include <pybind11/functional.h>

#include "tp/tp_types.h"
#include "tp/tp_segmenter.h"
#include "tp/tp_reassembler.h"
#include "tp/tp_manager.h"

namespace py = pybind11;
using namespace someip::tp;

void init_tp(py::module_& m) {
    auto tp = m.def_submodule("tp", "Transport Protocol bindings");

    py::enum_<TpResult>(tp, "TpResult")
        .value("SUCCESS", TpResult::SUCCESS)
        .value("MESSAGE_TOO_LARGE", TpResult::MESSAGE_TOO_LARGE)
        .value("SEGMENTATION_FAILED", TpResult::SEGMENTATION_FAILED)
        .value("REASSEMBLY_TIMEOUT", TpResult::REASSEMBLY_TIMEOUT)
        .value("INVALID_SEGMENT", TpResult::INVALID_SEGMENT)
        .value("SEQUENCE_ERROR", TpResult::SEQUENCE_ERROR)
        .value("NETWORK_ERROR", TpResult::NETWORK_ERROR)
        .value("RESOURCE_EXHAUSTED", TpResult::RESOURCE_EXHAUSTED)
        .value("TIMEOUT", TpResult::TIMEOUT);

    py::enum_<TpMessageType>(tp, "TpMessageType")
        .value("FIRST_SEGMENT", TpMessageType::FIRST_SEGMENT)
        .value("CONSECUTIVE_SEGMENT", TpMessageType::CONSECUTIVE_SEGMENT)
        .value("LAST_SEGMENT", TpMessageType::LAST_SEGMENT)
        .value("SINGLE_MESSAGE", TpMessageType::SINGLE_MESSAGE);

    py::enum_<TpTransferState>(tp, "TpTransferState")
        .value("IDLE", TpTransferState::IDLE)
        .value("SEGMENTING", TpTransferState::SEGMENTING)
        .value("SENDING", TpTransferState::SENDING)
        .value("WAITING_ACK", TpTransferState::WAITING_ACK)
        .value("RECEIVING", TpTransferState::RECEIVING)
        .value("REASSEMBLING", TpTransferState::REASSEMBLING)
        .value("COMPLETE", TpTransferState::COMPLETE)
        .value("FAILED", TpTransferState::FAILED)
        .value("TIMEOUT", TpTransferState::TIMEOUT);

    py::class_<TpConfig>(tp, "TpConfig")
        .def(py::init<>())
        .def_readwrite("max_segment_size", &TpConfig::max_segment_size)
        .def_readwrite("max_message_size", &TpConfig::max_message_size)
        .def_readwrite("max_retries", &TpConfig::max_retries)
        .def_readwrite("retry_timeout", &TpConfig::retry_timeout)
        .def_readwrite("reassembly_timeout", &TpConfig::reassembly_timeout)
        .def_readwrite("max_concurrent_transfers", &TpConfig::max_concurrent_transfers)
        .def_readwrite("enable_acknowledgments", &TpConfig::enable_acknowledgments);

    py::class_<TpSegmentHeader>(tp, "TpSegmentHeader")
        .def(py::init<>())
        .def_readwrite("message_length", &TpSegmentHeader::message_length)
        .def_readwrite("segment_offset", &TpSegmentHeader::segment_offset)
        .def_readwrite("segment_length", &TpSegmentHeader::segment_length)
        .def_readwrite("sequence_number", &TpSegmentHeader::sequence_number)
        .def_readwrite("message_type", &TpSegmentHeader::message_type);

    py::class_<TpSegment>(tp, "TpSegment")
        .def(py::init<>())
        .def_readwrite("header", &TpSegment::header)
        .def_readwrite("payload", &TpSegment::payload)
        .def_readwrite("retransmit_count", &TpSegment::retransmit_count);

    py::class_<TpStatistics>(tp, "TpStatistics")
        .def(py::init<>())
        .def_readonly("messages_segmented", &TpStatistics::messages_segmented)
        .def_readonly("messages_reassembled", &TpStatistics::messages_reassembled)
        .def_readonly("segments_sent", &TpStatistics::segments_sent)
        .def_readonly("segments_received", &TpStatistics::segments_received)
        .def_readonly("retransmissions", &TpStatistics::retransmissions)
        .def_readonly("timeouts", &TpStatistics::timeouts)
        .def_readonly("errors", &TpStatistics::errors);

    py::class_<TpSegmenter>(tp, "TpSegmenter")
        .def(py::init<const TpConfig&>(), py::arg("config") = TpConfig())
        .def("segment_message", &TpSegmenter::segment_message,
             py::arg("message"), py::arg("segments"))
        .def("update_config", &TpSegmenter::update_config, py::arg("config"));

    py::class_<TpReassembler>(tp, "TpReassembler")
        .def(py::init<const TpConfig&>(), py::arg("config") = TpConfig())
        .def("process_segment", &TpReassembler::process_segment,
             py::arg("segment"), py::arg("complete_message"))
        .def("is_reassembling", &TpReassembler::is_reassembling, py::arg("message_id"))
        .def("cancel_reassembly", &TpReassembler::cancel_reassembly, py::arg("message_id"))
        .def("process_timeouts", &TpReassembler::process_timeouts)
        .def("get_active_reassemblies", &TpReassembler::get_active_reassemblies)
        .def("update_config", &TpReassembler::update_config, py::arg("config"));

    py::class_<TpManager>(tp, "TpManager")
        .def(py::init<const TpConfig&>(), py::arg("config") = TpConfig())
        .def("initialize", &TpManager::initialize)
        .def("shutdown", &TpManager::shutdown, py::call_guard<py::gil_scoped_release>())
        .def("needs_segmentation", &TpManager::needs_segmentation, py::arg("message"))
        .def("segment_message", [](TpManager& mgr, const someip::Message& msg) {
            uint32_t transfer_id = 0;
            auto result = mgr.segment_message(msg, transfer_id);
            return py::make_tuple(result, transfer_id);
        }, py::arg("message"))
        .def("get_next_segment", [](TpManager& mgr, uint32_t transfer_id) {
            TpSegment segment;
            auto result = mgr.get_next_segment(transfer_id, segment);
            return py::make_tuple(result, segment);
        }, py::arg("transfer_id"))
        .def("handle_received_segment", [](TpManager& mgr, const TpSegment& segment) {
            std::vector<uint8_t> complete;
            bool done = mgr.handle_received_segment(segment, complete);
            return py::make_tuple(done, complete);
        }, py::arg("segment"))
        .def("cancel_transfer", &TpManager::cancel_transfer, py::arg("transfer_id"))
        .def("get_transfer_status", &TpManager::get_transfer_status, py::arg("transfer_id"))
        .def("set_completion_callback", &TpManager::set_completion_callback, py::arg("callback"))
        .def("set_progress_callback", &TpManager::set_progress_callback, py::arg("callback"))
        .def("set_message_callback", &TpManager::set_message_callback, py::arg("callback"))
        .def("process_timeouts", &TpManager::process_timeouts)
        .def("get_statistics", &TpManager::get_statistics)
        .def("update_config", &TpManager::update_config, py::arg("config"));
}
