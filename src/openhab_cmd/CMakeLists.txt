cmake_minimum_required(VERSION 3.8)
project(openhab_cmd)

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

# ── Python nodes ──────────────────────────────────────────────────────────
ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS
  openhab_cmd/openhab_get_state.py
  openhab_cmd/openhab_send_command.py
  openhab_cmd/openhab_subscriber.py
  openhab_cmd/openhab_publisher.py
  openhab_cmd/openhab_cmd_bridge_subscriber.py
  DESTINATION lib/${PROJECT_NAME}
)

# ── C++ executables ───────────────────────────────────────────────────────
add_executable(openhab_get_state_cpp
  src/openhab_get_state.cpp
)
ament_target_dependencies(openhab_get_state_cpp
  rclcpp openhab_msgs std_msgs
)

add_executable(openhab_send_command_cpp
  src/openhab_send_command.cpp
)
ament_target_dependencies(openhab_send_command_cpp
  rclcpp openhab_msgs std_msgs
)

add_executable(openhab_subscriber_cpp
  src/openhab_subscriber.cpp
)
ament_target_dependencies(openhab_subscriber_cpp
  rclcpp openhab_msgs std_msgs
)

add_executable(openhab_publisher_cpp
  src/openhab_publisher.cpp
)
ament_target_dependencies(openhab_publisher_cpp
  rclcpp openhab_msgs std_msgs
)

add_executable(openhab_cmd_bridge_subscriber_cpp
  src/openhab_cmd_bridge_subscriber.cpp
)
ament_target_dependencies(openhab_cmd_bridge_subscriber_cpp
  rclcpp openhab_msgs std_msgs
)
target_include_directories(openhab_cmd_bridge_subscriber_cpp PRIVATE
  ${CURL_INCLUDE_DIRS}
)
target_link_libraries(openhab_cmd_bridge_subscriber_cpp
  ${CURL_LIBRARIES}
)

install(TARGETS
  openhab_get_state_cpp
  openhab_send_command_cpp
  openhab_subscriber_cpp
  openhab_publisher_cpp
  openhab_cmd_bridge_subscriber_cpp
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY resource/
  DESTINATION share/${PROJECT_NAME}/resource
)

ament_package()
