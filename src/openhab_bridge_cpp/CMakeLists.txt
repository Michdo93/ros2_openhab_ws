cmake_minimum_required(VERSION 3.16)
project(openhab_bridge_cpp LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(diagnostic_msgs REQUIRED)
find_package(openhab_msgs REQUIRED)

# cpp-openhab-rest-client: installed (find_package) or directly from GitHub
find_package(OpenHABRestClientCpp QUIET)
if(NOT OpenHABRestClientCpp_FOUND)
  include(FetchContent)
  set(OPENHAB_BUILD_TESTS OFF CACHE BOOL "" FORCE)
  FetchContent_Declare(cpp_openhab_rest_client
    GIT_REPOSITORY https://github.com/Michdo93/cpp-openhab-rest-client.git
    GIT_TAG        2.0.0)
  FetchContent_MakeAvailable(cpp_openhab_rest_client)
endif()

add_executable(openhab_bridge src/openhab_bridge.cpp)
# Modern CMake targets – ament_target_dependencies() no longer exists in Lyrical
target_link_libraries(openhab_bridge openhab::rest_client_cpp rclcpp::rclcpp
  ${std_msgs_TARGETS} ${diagnostic_msgs_TARGETS} ${openhab_msgs_TARGETS})

install(TARGETS openhab_bridge DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})
ament_package()
