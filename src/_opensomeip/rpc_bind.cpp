#include <pybind11/pybind11.h>

namespace py = pybind11;

void init_rpc(py::module_& m) {
    // RPC bindings will be added here once opensomeip headers are
    // available via the git submodule.
    //
    // Planned bindings:
    //   - py::class_<RpcClient> with start/stop/call (GIL released),
    //     call_async (callback acquires GIL)
    //   - py::class_<RpcServer> with start/stop/register_method
    //     (handler trampoline acquires GIL)
}
