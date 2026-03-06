find_package(pybind11 CONFIG REQUIRED)

set(BINDING_SOURCES
    module.cpp
    types_bind.cpp
    message_bind.cpp
    serialization_bind.cpp
    transport_bind.cpp
    sd_bind.cpp
    rpc_bind.cpp
    events_bind.cpp
    tp_bind.cpp
    e2e_bind.cpp
    exceptions.cpp
)

pybind11_add_module(_opensomeip ${BINDING_SOURCES})

target_include_directories(_opensomeip PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Link against opensomeip static libraries when the submodule is present
if(TARGET someip-core)
    target_link_libraries(_opensomeip PRIVATE
        someip-core
        someip-serialization
        someip-transport
        someip-rpc
        someip-sd
        someip-events
        someip-tp
    )
endif()

install(TARGETS _opensomeip DESTINATION opensomeip)
