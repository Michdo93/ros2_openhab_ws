/**
 * openhab_send_command.cpp
 * ========================
 * Generic C++ service client: send a command to ANY openHAB item.
 *
 * Parameters:
 *   item_name  (string, required)
 *   item_type  (string, default: "Switch")
 *   command    (string, required)
 *
 * Usage:
 *   ros2 run openhab_cmd openhab_send_command_cpp \
 *       --ros-args -p item_name:=LivingRoomLight \
 *                  -p item_type:=Switch \
 *                  -p command:=ON
 */

#include <rclcpp/rclcpp.hpp>
#include <string>

#include "openhab_msgs/srv/send_color_command.hpp"
#include "openhab_msgs/srv/send_contact_command.hpp"
#include "openhab_msgs/srv/send_date_time_command.hpp"
#include "openhab_msgs/srv/send_dimmer_command.hpp"
#include "openhab_msgs/srv/send_location_command.hpp"
#include "openhab_msgs/srv/send_number_command.hpp"
#include "openhab_msgs/srv/send_player_command.hpp"
#include "openhab_msgs/srv/send_rollershutter_command.hpp"
#include "openhab_msgs/srv/send_string_command.hpp"
#include "openhab_msgs/srv/send_switch_command.hpp"

class OpenHABSendCommandClient : public rclcpp::Node {
public:
    OpenHABSendCommandClient() : Node("openhab_send_command_cpp") {
        declare_parameter("item_name", "");
        declare_parameter("item_type", "Switch");
        declare_parameter("command",   "");

        item_name_ = get_parameter("item_name").as_string();
        item_type_ = get_parameter("item_type").as_string();
        command_   = get_parameter("command").as_string();

        if (item_name_.empty()) { RCLCPP_ERROR(get_logger(), "'item_name' required!"); return; }
        if (command_.empty())   { RCLCPP_ERROR(get_logger(), "'command' required!"); return; }

        callService();
    }

private:
    std::string item_name_, item_type_, command_;

    template<typename SrvT>
    void doSend(const std::string& srv_name) {
        auto client = create_client<SrvT>(srv_name);
        while (!client->wait_for_service(std::chrono::seconds(1))) { if (!rclcpp::ok()) return; }
        auto req = std::make_shared<typename SrvT::Request>();
        req->item_name = item_name_;
        req->command   = command_;
        RCLCPP_INFO(get_logger(), "Sending '%s' -> '%s' (%s)",
            command_.c_str(), item_name_.c_str(), item_type_.c_str());
        auto future = client->async_send_request(req);
        if (rclcpp::spin_until_future_complete(get_node_base_interface(), future)
            == rclcpp::FutureReturnCode::SUCCESS) {
            auto resp = future.get();
            if (resp->success) RCLCPP_INFO(get_logger(), "OK: %s", resp->message.c_str());
            else               RCLCPP_ERROR(get_logger(), "Failed: %s", resp->message.c_str());
        }
    }

    void callService() {
        if      (item_type_ == "Color")         doSend<openhab_msgs::srv::SendColorCommand>("/openhab/send_command/color");
        else if (item_type_ == "Contact")       doSend<openhab_msgs::srv::SendContactCommand>("/openhab/send_command/contact");
        else if (item_type_ == "DateTime")      doSend<openhab_msgs::srv::SendDateTimeCommand>("/openhab/send_command/datetime");
        else if (item_type_ == "Dimmer")        doSend<openhab_msgs::srv::SendDimmerCommand>("/openhab/send_command/dimmer");
        else if (item_type_ == "Location")      doSend<openhab_msgs::srv::SendLocationCommand>("/openhab/send_command/location");
        else if (item_type_ == "Number")        doSend<openhab_msgs::srv::SendNumberCommand>("/openhab/send_command/number");
        else if (item_type_ == "Player")        doSend<openhab_msgs::srv::SendPlayerCommand>("/openhab/send_command/player");
        else if (item_type_ == "Rollershutter") doSend<openhab_msgs::srv::SendRollershutterCommand>("/openhab/send_command/rollershutter");
        else if (item_type_ == "String")        doSend<openhab_msgs::srv::SendStringCommand>("/openhab/send_command/string");
        else if (item_type_ == "Switch")        doSend<openhab_msgs::srv::SendSwitchCommand>("/openhab/send_command/switch");
        else RCLCPP_ERROR(get_logger(), "Unknown item_type '%s'", item_type_.c_str());
    }
};

int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<OpenHABSendCommandClient>());
    rclcpp::shutdown();
    return 0;
}
