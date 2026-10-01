cmake_minimum_required(VERSION 3.8)
project(openhab_static_examples)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(openhab_msgs REQUIRED)
find_package(std_msgs REQUIRED)

ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS
  openhab_static_examples/call_get_state_client.py
  openhab_static_examples/call_subscriber.py
  openhab_static_examples/color_get_state_client.py
  openhab_static_examples/color_send_command_client.py
  openhab_static_examples/color_subscriber.py
  openhab_static_examples/contact_get_state_client.py
  openhab_static_examples/contact_send_command_client.py
  openhab_static_examples/contact_subscriber.py
  openhab_static_examples/datetime_get_state_client.py
  openhab_static_examples/datetime_send_command_client.py
  openhab_static_examples/datetime_subscriber.py
  openhab_static_examples/dimmer_get_state_client.py
  openhab_static_examples/dimmer_send_command_client.py
  openhab_static_examples/dimmer_subscriber.py
  openhab_static_examples/image_get_state_client.py
  openhab_static_examples/image_subscriber.py
  openhab_static_examples/location_get_state_client.py
  openhab_static_examples/location_send_command_client.py
  openhab_static_examples/location_subscriber.py
  openhab_static_examples/number_get_state_client.py
  openhab_static_examples/number_send_command_client.py
  openhab_static_examples/number_subscriber.py
  openhab_static_examples/player_get_state_client.py
  openhab_static_examples/player_send_command_client.py
  openhab_static_examples/player_subscriber.py
  openhab_static_examples/rollershutter_get_state_client.py
  openhab_static_examples/rollershutter_send_command_client.py
  openhab_static_examples/rollershutter_subscriber.py
  openhab_static_examples/string_get_state_client.py
  openhab_static_examples/string_send_command_client.py
  openhab_static_examples/string_subscriber.py
  openhab_static_examples/switch_get_state_client.py
  openhab_static_examples/switch_send_command_client.py
  openhab_static_examples/switch_subscriber.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY resource/
  DESTINATION share/${PROJECT_NAME}/resource
)

ament_package()
