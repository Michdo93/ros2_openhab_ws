cmake_minimum_required(VERSION 3.8)
project(openhab_events)

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
find_package(nlohmann_json REQUIRED)

# ── C++ SSE Publisher ─────────────────────────────────────────────────────
add_executable(openhab_event_publisher_cpp
  src/openhab_event_publisher.cpp
)
ament_target_dependencies(openhab_event_publisher_cpp
  rclcpp openhab_msgs std_msgs
)
target_include_directories(openhab_event_publisher_cpp PRIVATE
  ${CURL_INCLUDE_DIRS}
)
target_link_libraries(openhab_event_publisher_cpp
  ${CURL_LIBRARIES}
  nlohmann_json::nlohmann_json
)

install(TARGETS openhab_event_publisher_cpp
  DESTINATION lib/${PROJECT_NAME}
)

# ── Python nodes ──────────────────────────────────────────────────────────
ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS
  openhab_events/openhab_event_publisher.py
  openhab_events/openhab_event_publisher_async.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY resource/
  DESTINATION share/${PROJECT_NAME}/resource
)

ament_package()
