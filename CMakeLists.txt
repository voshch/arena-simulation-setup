cmake_minimum_required(VERSION 3.5)
project(simulation-setup)

# Default to C++17
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

# Check Compiler
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)

# Python setup
ament_python_install_package(${PROJECT_NAME})

# Include directories
include_directories(include)

# Set dependencies 
set(dependencies
  ament_cmake
)

ament_export_include_directories(include)
ament_export_dependencies(${dependencies})

ament_package()
