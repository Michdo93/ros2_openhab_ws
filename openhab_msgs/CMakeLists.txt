cmake_minimum_required(VERSION 3.8)
project(openhab_msgs)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  # ── State Messages ──────────────────────────────────────────────────────
  "msg/CallState.msg"
  "msg/ColorState.msg"
  "msg/ContactState.msg"
  "msg/DateTimeState.msg"
  "msg/DimmerState.msg"
  "msg/ImageState.msg"
  "msg/LocationState.msg"
  "msg/NumberState.msg"
  "msg/PlayerState.msg"
  "msg/RollershutterState.msg"
  "msg/StringState.msg"
  "msg/SwitchState.msg"
  # ── Command Messages ─────────────────────────────────────────────────────
  "msg/ColorCommand.msg"
  "msg/ContactCommand.msg"
  "msg/DateTimeCommand.msg"
  "msg/DimmerCommand.msg"
  "msg/LocationCommand.msg"
  "msg/NumberCommand.msg"
  "msg/PlayerCommand.msg"
  "msg/RollershutterCommand.msg"
  "msg/StringCommand.msg"
  "msg/SwitchCommand.msg"
  # ── Services: Get Item State ─────────────────────────────────────────────
  "srv/GetCallState.srv"
  "srv/GetColorState.srv"
  "srv/GetContactState.srv"
  "srv/GetDateTimeState.srv"
  "srv/GetDimmerState.srv"
  "srv/GetImageState.srv"
  "srv/GetLocationState.srv"
  "srv/GetNumberState.srv"
  "srv/GetPlayerState.srv"
  "srv/GetRollershutterState.srv"
  "srv/GetStringState.srv"
  "srv/GetSwitchState.srv"
  # ── Services: Send Command ───────────────────────────────────────────────
  "srv/SendColorCommand.srv"
  "srv/SendContactCommand.srv"
  "srv/SendDateTimeCommand.srv"
  "srv/SendDimmerCommand.srv"
  "srv/SendLocationCommand.srv"
  "srv/SendNumberCommand.srv"
  "srv/SendPlayerCommand.srv"
  "srv/SendRollershutterCommand.srv"
  "srv/SendStringCommand.srv"
  "srv/SendSwitchCommand.srv"
  DEPENDENCIES std_msgs
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
