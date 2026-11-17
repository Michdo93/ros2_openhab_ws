cmake_minimum_required(VERSION 3.8)
project(openhab_msgs)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/ItemState.msg"
  "msg/ItemCommand.msg"
  "srv/GetItem.srv"
  "srv/SendCommand.srv"
  "srv/ListItems.srv"
  DEPENDENCIES std_msgs
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
