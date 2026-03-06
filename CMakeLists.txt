cmake_minimum_required(VERSION 3.20)
project(opensomeip-python LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Platform backend selection: only POSIX and Win32.
if(WIN32)
    set(OPENSOMEIP_PLATFORM "WIN32" CACHE STRING "opensomeip platform backend")
else()
    set(OPENSOMEIP_PLATFORM "POSIX" CACHE STRING "opensomeip platform backend")
endif()

# Disable RTOS backends
set(OPENSOMEIP_ENABLE_FREERTOS OFF CACHE BOOL "" FORCE)
set(OPENSOMEIP_ENABLE_THREADX OFF CACHE BOOL "" FORCE)
set(OPENSOMEIP_ENABLE_ZEPHYR OFF CACHE BOOL "" FORCE)
set(OPENSOMEIP_ENABLE_LWIP OFF CACHE BOOL "" FORCE)

# Build opensomeip C++ library from submodule
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/extern/opensomeip/CMakeLists.txt")
    add_subdirectory(extern/opensomeip)
endif()

# Build the pybind11 extension module
add_subdirectory(src/_opensomeip)
