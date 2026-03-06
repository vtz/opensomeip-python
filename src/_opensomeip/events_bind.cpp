#include <pybind11/pybind11.h>

namespace py = pybind11;

void init_events(py::module_& m) {
    // Event bindings will be added here once opensomeip headers are
    // available via the git submodule.
    //
    // Planned bindings:
    //   - py::class_<EventPublisher> with start/stop/register_event/notify/set_field
    //     (GIL released for blocking ops)
    //   - py::class_<EventSubscriber> with start/stop/subscribe
    //     (notification and status callbacks acquire GIL)
}
