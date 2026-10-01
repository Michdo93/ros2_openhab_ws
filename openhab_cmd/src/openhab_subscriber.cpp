/**
 * openhab_subscriber.cpp
 * ======================
 * Generic C++ subscriber: subscribe to /openhab/state/<item_name>
 * and print state changes to the terminal.
 *
 * Parameters:
 *   item_name  (string, required)
 *   item_type  (string, default: "Switch")
 *
 * Usage:
 *   ros2 run openhab_cmd openhab_subscriber_cpp \
 *       --ros-args -p item_name:=LivingRoomLight -p item_type:=Switch
 */

#include <rclcpp/rclcpp.hpp>
#include <string>
#include <memory>

#include "openhab_msgs/msg/call_state.hpp"
#include "openhab_msgs/msg/color_state.hpp"
#include "openhab_msgs/msg/contact_state.hpp"
#include "openhab_msgs/msg/date_time_state.hpp"
#include "openhab_msgs/msg/dimmer_state.hpp"
#include "openhab_msgs/msg/image_state.hpp"
#include "openhab_msgs/msg/location_state.hpp"
#include "openhab_msgs/msg/number_state.hpp"
#include "openhab_msgs/msg/player_state.hpp"
#include "openhab_msgs/msg/rollershutter_state.hpp"
#include "openhab_msgs/msg/string_state.hpp"
#include "openhab_msgs/msg/switch_state.hpp"

class OpenHABSubscriber : public rclcpp::Node {
public:
    OpenHABSubscriber() : Node("openhab_subscriber_cpp") {
        declare_parameter("item_name", "");
        declare_parameter("item_type", "Switch");

        auto item_name = get_parameter("item_name").as_string();
        auto item_type = get_parameter("item_type").as_string();

        if (item_name.empty()) {
            RCLCPP_ERROR(get_logger(), "Parameter 'item_name' is required!");
            return;
        }

        std::string topic = "/openhab/state/" + item_name;
        RCLCPP_INFO(get_logger(), "Subscribing to %s [%s]", topic.c_str(), item_type.c_str());

        if (item_type == "Switch") {
            sub_ = create_subscription<openhab_msgs::msg::SwitchState>(topic, 10,
                [this, item_type](openhab_msgs::msg::SwitchState::SharedPtr msg) {
                    RCLCPP_INFO(get_logger(), "[Switch] %s = %s", msg->item_name.c_str(), msg->state.c_str());
                });
        } else if (item_type == "Dimmer") {
            sub_ = create_subscription<openhab_msgs::msg::DimmerState>(topic, 10,
                [this](openhab_msgs::msg::DimmerState::SharedPtr msg) {
                    RCLCPP_INFO(get_logger(), "[Dimmer] %s = %.1f%%", msg->item_name.c_str(), msg->state);
                });
        } else if (item_type == "Color") {
            sub_ = create_subscription<openhab_msgs::msg::ColorState>(topic, 10,
                [this](openhab_msgs::msg::ColorState::SharedPtr msg) {
                    RCLCPP_INFO(get_logger(), "[Color] %s = %s (H:%.1f S:%.1f B:%.1f)",
                        msg->item_name.c_str(), msg->state.c_str(),
                        msg->hue, msg->saturation, msg->brightness);
                });
        } else if (item_type == "Contact") {
            sub_ = create_subscription<openhab_msgs::msg::ContactState>(topic, 10,
                [this](openhab_msgs::msg::ContactState::SharedPtr msg) {
                    RCLCPP_INFO(get_logger(), "[Contact] %s = %s", msg->item_name.c_str(), msg->state.c_str());
                });
        } else if (item_type == "DateTime") {
            sub_ = create_subscription<openhab_msgs::msg::DateTimeState>(topic, 10,
                [this](openhab_msgs::msg::DateTimeState::SharedPtr msg) {
                    RCLCPP_INFO(get_logger(), "[DateTime] %s = %s", msg->item_name.c_str(), msg->state.c_str());
                });
        } else if (item_type == "Image") {
            sub_ = create_subscription<openhab_msgs::msg::ImageState>(topic, 10,
                [this](openhab_msgs::msg::ImageState::SharedPtr msg) {
                    RCLCPP_INFO(get_logger(), "[Image] %s updated", msg->item_name.c_str());
                });
        } else if (item_type == "Location") {
            sub_ = create_subscription<openhab_msgs::msg::LocationState>(topic, 10,
                [this](openhab_msgs::msg::LocationState::SharedPtr msg) {
                    RCLCPP_INFO(get_logger(), "[Location] %s = lat:%.6f lon:%.6f alt:%.2f",
                        msg->item_name.c_str(), msg->latitude, msg->longitude, msg->altitude);
                });
        } else if (item_type == "Number") {
            sub_ = create_subscription<openhab_msgs::msg::NumberState>(topic, 10,
                [this](openhab_msgs::msg::NumberState::SharedPtr msg) {
                    RCLCPP_INFO(get_logger(), "[Number] %s = %f %s",
                        msg->item_name.c_str(), msg->state, msg->unit.c_str());
                });
        } else if (item_type == "Player") {
            sub_ = create_subscription<openhab_msgs::msg::PlayerState>(topic, 10,
                [this](openhab_msgs::msg::PlayerState::SharedPtr msg) {
                    RCLCPP_INFO(get_logger(), "[Player] %s = %s", msg->item_name.c_str(), msg->state.c_str());
                });
        } else if (item_type == "Rollershutter") {
            sub_ = create_subscription<openhab_msgs::msg::RollershutterState>(topic, 10,
                [this](openhab_msgs::msg::RollershutterState::SharedPtr msg) {
                    RCLCPP_INFO(get_logger(), "[Rollershutter] %s = %.1f%%", msg->item_name.c_str(), msg->state);
                });
        } else if (item_type == "Call") {
            sub_ = create_subscription<openhab_msgs::msg::CallState>(topic, 10,
                [this](openhab_msgs::msg::CallState::SharedPtr msg) {
                    RCLCPP_INFO(get_logger(), "[Call] %s = %s", msg->item_name.c_str(), msg->state.c_str());
                });
        } else {
            // Fallback: String
            sub_ = create_subscription<openhab_msgs::msg::StringState>(topic, 10,
                [this](openhab_msgs::msg::StringState::SharedPtr msg) {
                    RCLCPP_INFO(get_logger(), "[String] %s = %s", msg->item_name.c_str(), msg->state.c_str());
                });
        }
    }

private:
    rclcpp::SubscriptionBase::SharedPtr sub_;
};

int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<OpenHABSubscriber>());
    rclcpp::shutdown();
    return 0;
}
