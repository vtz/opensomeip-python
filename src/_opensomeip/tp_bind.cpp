#include <pybind11/pybind11.h>

namespace py = pybind11;

void init_tp(py::module_& m) {
    // Transport Protocol bindings will be added here once opensomeip
    // headers are available via the git submodule.
    //
    // Planned bindings:
    //   - py::class_<TpManager> with send (GIL released),
    //     reassembly callbacks (GIL acquired)
    //   - py::class_<TpSegmenter>
    //   - py::class_<TpReassembler>
}
