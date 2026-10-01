cmake_minimum_required(VERSION 3.8)
project(openhab_rest)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(openhab_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(CURL REQUIRED)

# ── C++ Service Server ────────────────────────────────────────────────────
add_executable(openhab_rest_server_cpp
  src/openhab_rest_server.cpp
)
ament_target_dependencies(openhab_rest_server_cpp
  rclcpp openhab_msgs std_msgs
)
target_include_directories(openhab_rest_server_cpp PRIVATE
  ${CURL_INCLUDE_DIRS}
)
target_link_libraries(openhab_rest_server_cpp
  ${CURL_LIBRARIES}
)

install(TARGETS openhab_rest_server_cpp
  DESTINATION lib/${PROJECT_NAME}
)

# ── Python nodes ──────────────────────────────────────────────────────────
ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS
  openhab_rest/openhab_rest_server.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY resource/
  DESTINATION share/${PROJECT_NAME}/resource
)

ament_package()
