/**
 * openhab_get_state.cpp
 * =====================
 * Generic C++ service client: query the state of ANY openHAB item.
 *
 * Parameters:
 *   item_name  (string, required)
 *   item_type  (string, default: "Switch")
 *              Call|Color|Contact|DateTime|Dimmer|Image|Location|
 *              Number|Player|Rollershutter|String|Switch
 *
 * Usage:
 *   ros2 run openhab_cmd openhab_get_state_cpp \
 *       --ros-args -p item_name:=LivingRoomLight -p item_type:=Switch
 */

#include <rclcpp/rclcpp.hpp>
#include <memory>
#include <string>

#include "openhab_msgs/srv/get_call_state.hpp"
#include "openhab_msgs/srv/get_color_state.hpp"
#include "openhab_msgs/srv/get_contact_state.hpp"
#include "openhab_msgs/srv/get_date_time_state.hpp"
#include "openhab_msgs/srv/get_dimmer_state.hpp"
#include "openhab_msgs/srv/get_image_state.hpp"
#include "openhab_msgs/srv/get_location_state.hpp"
#include "openhab_msgs/srv/get_number_state.hpp"
#include "openhab_msgs/srv/get_player_state.hpp"
#include "openhab_msgs/srv/get_rollershutter_state.hpp"
#include "openhab_msgs/srv/get_string_state.hpp"
#include "openhab_msgs/srv/get_switch_state.hpp"

class OpenHABGetStateClient : public rclcpp::Node {
public:
    OpenHABGetStateClient() : Node("openhab_get_state_cpp") {
        declare_parameter("item_name", "");
        declare_parameter("item_type", "Switch");

        item_name_ = get_parameter("item_name").as_string();
        item_type_ = get_parameter("item_type").as_string();

        if (item_name_.empty()) {
            RCLCPP_ERROR(get_logger(), "Parameter 'item_name' is required!");
            return;
        }
        callService();
    }

private:
    std::string item_name_;
    std::string item_type_;

    template<typename SrvT>
    void doCall(const std::string& service_name) {
        auto client = create_client<SrvT>(service_name);
        RCLCPP_INFO(get_logger(), "Waiting for %s ...", service_name.c_str());
        while (!client->wait_for_service(std::chrono::seconds(1))) {
            if (!rclcpp::ok()) return;
        }
        auto req = std::make_shared<typename SrvT::Request>();
        req->item_name = item_name_;
        auto future = client->async_send_request(req);

        if (rclcpp::spin_until_future_complete(
                this->get_node_base_interface(), future)
            == rclcpp::FutureReturnCode::SUCCESS)
        {
            auto resp = future.get();
            if (resp->success) {
                RCLCPP_INFO(get_logger(), "[%s] %s state:", item_type_.c_str(), item_name_.c_str());
                RCLCPP_INFO(get_logger(), "  state: %s", resp->state.state.c_str());
                // Type-specific extra fields
                if (item_type_ == "Color") {
                    RCLCPP_INFO(get_logger(), "  hue  : %.2f", resp->state.hue);
                    RCLCPP_INFO(get_logger(), "  sat  : %.2f", resp->state.saturation);
                    RCLCPP_INFO(get_logger(), "  bri  : %.2f", resp->state.brightness);
                } else if (item_type_ == "Location") {
                    RCLCPP_INFO(get_logger(), "  lat  : %.6f", resp->state.latitude);
                    RCLCPP_INFO(get_logger(), "  lon  : %.6f", resp->state.longitude);
                    RCLCPP_INFO(get_logger(), "  alt  : %.2f",  resp->state.altitude);
                } else if (item_type_ == "Number") {
                    RCLCPP_INFO(get_logger(), "  unit : %s", resp->state.unit.c_str());
                }
            } else {
                RCLCPP_ERROR(get_logger(), "Failed: %s", resp->message.c_str());
            }
        } else {
            RCLCPP_ERROR(get_logger(), "Service call timed out.");
        }
    }

    // Specialised overloads for types where state is a float, not string
    void callDimmer() {
        auto client = create_client<openhab_msgs::srv::GetDimmerState>("/openhab/get_state/dimmer");
        while (!client->wait_for_service(std::chrono::seconds(1))) { if (!rclcpp::ok()) return; }
        auto req = std::make_shared<openhab_msgs::srv::GetDimmerState::Request>();
        req->item_name = item_name_;
        auto future = client->async_send_request(req);
        if (rclcpp::spin_until_future_complete(get_node_base_interface(), future) == rclcpp::FutureReturnCode::SUCCESS) {
            auto resp = future.get();
            if (resp->success)
                RCLCPP_INFO(get_logger(), "[Dimmer] %s = %.1f%%", item_name_.c_str(), resp->state.state);
            else RCLCPP_ERROR(get_logger(), "Failed: %s", resp->message.c_str());
        }
    }

    void callRollershutter() {
        auto client = create_client<openhab_msgs::srv::GetRollershutterState>("/openhab/get_state/rollershutter");
        while (!client->wait_for_service(std::chrono::seconds(1))) { if (!rclcpp::ok()) return; }
        auto req = std::make_shared<openhab_msgs::srv::GetRollershutterState::Request>();
        req->item_name = item_name_;
        auto future = client->async_send_request(req);
        if (rclcpp::spin_until_future_complete(get_node_base_interface(), future) == rclcpp::FutureReturnCode::SUCCESS) {
            auto resp = future.get();
            if (resp->success)
                RCLCPP_INFO(get_logger(), "[Rollershutter] %s = %.1f%%", item_name_.c_str(), resp->state.state);
            else RCLCPP_ERROR(get_logger(), "Failed: %s", resp->message.c_str());
        }
    }

    void callNumber() {
        auto client = create_client<openhab_msgs::srv::GetNumberState>("/openhab/get_state/number");
        while (!client->wait_for_service(std::chrono::seconds(1))) { if (!rclcpp::ok()) return; }
        auto req = std::make_shared<openhab_msgs::srv::GetNumberState::Request>();
        req->item_name = item_name_;
        auto future = client->async_send_request(req);
        if (rclcpp::spin_until_future_complete(get_node_base_interface(), future) == rclcpp::FutureReturnCode::SUCCESS) {
            auto resp = future.get();
            if (resp->success)
                RCLCPP_INFO(get_logger(), "[Number] %s = %f %s", item_name_.c_str(), resp->state.state, resp->state.unit.c_str());
            else RCLCPP_ERROR(get_logger(), "Failed: %s", resp->message.c_str());
        }
    }

    void callService() {
        if      (item_type_ == "Call")          doCall<openhab_msgs::srv::GetCallState>("/openhab/get_state/call");
        else if (item_type_ == "Color")         doCall<openhab_msgs::srv::GetColorState>("/openhab/get_state/color");
        else if (item_type_ == "Contact")       doCall<openhab_msgs::srv::GetContactState>("/openhab/get_state/contact");
        else if (item_type_ == "DateTime")      doCall<openhab_msgs::srv::GetDateTimeState>("/openhab/get_state/datetime");
        else if (item_type_ == "Dimmer")        callDimmer();
        else if (item_type_ == "Image")         doCall<openhab_msgs::srv::GetImageState>("/openhab/get_state/image");
        else if (item_type_ == "Location")      doCall<openhab_msgs::srv::GetLocationState>("/openhab/get_state/location");
        else if (item_type_ == "Number")        callNumber();
        else if (item_type_ == "Player")        doCall<openhab_msgs::srv::GetPlayerState>("/openhab/get_state/player");
        else if (item_type_ == "Rollershutter") callRollershutter();
        else if (item_type_ == "String")        doCall<openhab_msgs::srv::GetStringState>("/openhab/get_state/string");
        else if (item_type_ == "Switch")        doCall<openhab_msgs::srv::GetSwitchState>("/openhab/get_state/switch");
        else RCLCPP_ERROR(get_logger(), "Unknown item_type '%s'", item_type_.c_str());
    }
};

int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<OpenHABGetStateClient>());
    rclcpp::shutdown();
    return 0;
}
