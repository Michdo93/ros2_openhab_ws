/**
 * openhab_publisher.cpp
 * =====================
 * Generic C++ publisher: publish openHAB commands on
 * /openhab/command/<item_name>.
 *
 * Parameters:
 *   item_name      (string,  required)
 *   item_type      (string,  default: "Switch")
 *                  Color|Contact|DateTime|Dimmer|Location|Number|
 *                  Player|Rollershutter|String|Switch
 *   command        (string,  required)
 *   publish_once   (bool,    default: true)
 *   rate_hz        (double,  default: 1.0)
 *
 * Usage:
 *   ros2 run openhab_cmd openhab_publisher_cpp \
 *       --ros-args -p item_name:=LivingRoomLight \
 *                  -p item_type:=Switch \
 *                  -p command:=ON
 */

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/header.hpp>
#include <string>
#include <memory>
#include <chrono>
#include <sstream>

#include "openhab_msgs/msg/color_command.hpp"
#include "openhab_msgs/msg/contact_command.hpp"
#include "openhab_msgs/msg/date_time_command.hpp"
#include "openhab_msgs/msg/dimmer_command.hpp"
#include "openhab_msgs/msg/location_command.hpp"
#include "openhab_msgs/msg/number_command.hpp"
#include "openhab_msgs/msg/player_command.hpp"
#include "openhab_msgs/msg/rollershutter_command.hpp"
#include "openhab_msgs/msg/string_command.hpp"
#include "openhab_msgs/msg/switch_command.hpp"

class OpenHABPublisher : public rclcpp::Node {
public:
    OpenHABPublisher() : Node("openhab_publisher_cpp"), published_(false) {
        declare_parameter("item_name",    "");
        declare_parameter("item_type",    "Switch");
        declare_parameter("command",      "");
        declare_parameter("publish_once", true);
        declare_parameter("rate_hz",      1.0);

        item_name_    = get_parameter("item_name").as_string();
        item_type_    = get_parameter("item_type").as_string();
        command_      = get_parameter("command").as_string();
        publish_once_ = get_parameter("publish_once").as_bool();
        double rate   = get_parameter("rate_hz").as_double();

        if (item_name_.empty()) {
            RCLCPP_ERROR(get_logger(), "Parameter 'item_name' is required!");
            return;
        }
        if (command_.empty()) {
            RCLCPP_ERROR(get_logger(), "Parameter 'command' is required!");
            return;
        }

        std::string topic = "/openhab/command/" + item_name_;
        setupPublisher(topic);

        double period = publish_once_ ? 0.2 : (1.0 / std::max(rate, 0.001));
        timer_ = create_timer(
            std::chrono::duration<double>(period),
            std::bind(&OpenHABPublisher::timerCb, this)
        );

        RCLCPP_INFO(get_logger(),
            "Publishing to %s [%s]  cmd=%s  once=%s",
            topic.c_str(), item_type_.c_str(), command_.c_str(),
            publish_once_ ? "true" : "false");
    }

private:
    std::string item_name_, item_type_, command_;
    bool publish_once_, published_;
    rclcpp::TimerBase::SharedPtr timer_;
    rclcpp::PublisherBase::SharedPtr pub_;

    std_msgs::msg::Header makeHeader() {
        std_msgs::msg::Header h;
        h.stamp = get_clock()->now();
        h.frame_id = "";
        return h;
    }

    void setupPublisher(const std::string& topic) {
        if      (item_type_ == "Switch")        pub_ = create_publisher<openhab_msgs::msg::SwitchCommand>(topic, 10);
        else if (item_type_ == "Dimmer")        pub_ = create_publisher<openhab_msgs::msg::DimmerCommand>(topic, 10);
        else if (item_type_ == "Color")         pub_ = create_publisher<openhab_msgs::msg::ColorCommand>(topic, 10);
        else if (item_type_ == "Contact")       pub_ = create_publisher<openhab_msgs::msg::ContactCommand>(topic, 10);
        else if (item_type_ == "DateTime")      pub_ = create_publisher<openhab_msgs::msg::DateTimeCommand>(topic, 10);
        else if (item_type_ == "Location")      pub_ = create_publisher<openhab_msgs::msg::LocationCommand>(topic, 10);
        else if (item_type_ == "Number")        pub_ = create_publisher<openhab_msgs::msg::NumberCommand>(topic, 10);
        else if (item_type_ == "Player")        pub_ = create_publisher<openhab_msgs::msg::PlayerCommand>(topic, 10);
        else if (item_type_ == "Rollershutter") pub_ = create_publisher<openhab_msgs::msg::RollershutterCommand>(topic, 10);
        else                                     pub_ = create_publisher<openhab_msgs::msg::StringCommand>(topic, 10);
    }

    void timerCb() {
        publishCommand();
        published_ = true;
        if (publish_once_) {
            timer_->cancel();
            RCLCPP_INFO(get_logger(), "Published once – shutting down.");
            rclcpp::shutdown();
        }
    }

    void publishCommand() {
        std::string t = item_type_;

        if (t == "Switch") {
            openhab_msgs::msg::SwitchCommand msg;
            msg.header = makeHeader(); msg.item_name = item_name_; msg.command = command_;
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::SwitchCommand>>(pub_)->publish(msg);

        } else if (t == "Dimmer") {
            openhab_msgs::msg::DimmerCommand msg;
            msg.header = makeHeader(); msg.item_name = item_name_; msg.command_type = command_;
            try { msg.percent = std::stof(command_); } catch (...) { msg.percent = 0.0f; }
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::DimmerCommand>>(pub_)->publish(msg);

        } else if (t == "Color") {
            openhab_msgs::msg::ColorCommand msg;
            msg.header = makeHeader(); msg.item_name = item_name_; msg.command_type = command_;
            try {
                auto p1 = command_.find(',');
                auto p2 = command_.find(',', p1 + 1);
                if (p1 != std::string::npos && p2 != std::string::npos) {
                    msg.hue        = std::stof(command_.substr(0, p1));
                    msg.saturation = std::stof(command_.substr(p1 + 1, p2 - p1 - 1));
                    msg.brightness = std::stof(command_.substr(p2 + 1));
                }
            } catch (...) {}
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::ColorCommand>>(pub_)->publish(msg);

        } else if (t == "Contact") {
            openhab_msgs::msg::ContactCommand msg;
            msg.header = makeHeader(); msg.item_name = item_name_; msg.command = command_;
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::ContactCommand>>(pub_)->publish(msg);

        } else if (t == "DateTime") {
            openhab_msgs::msg::DateTimeCommand msg;
            msg.header = makeHeader(); msg.item_name = item_name_; msg.command = command_;
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::DateTimeCommand>>(pub_)->publish(msg);

        } else if (t == "Location") {
            openhab_msgs::msg::LocationCommand msg;
            msg.header = makeHeader(); msg.item_name = item_name_;
            try {
                auto p1 = command_.find(',');
                auto p2 = command_.find(',', p1 + 1);
                if (p1 != std::string::npos) {
                    msg.latitude  = std::stod(command_.substr(0, p1));
                    msg.longitude = std::stod(command_.substr(p1 + 1, p2 == std::string::npos ? std::string::npos : p2 - p1 - 1));
                    if (p2 != std::string::npos) msg.altitude = std::stod(command_.substr(p2 + 1));
                }
            } catch (...) {}
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::LocationCommand>>(pub_)->publish(msg);

        } else if (t == "Number") {
            openhab_msgs::msg::NumberCommand msg;
            msg.header = makeHeader(); msg.item_name = item_name_;
            auto sp = command_.find(' ');
            try {
                msg.value = std::stod(sp == std::string::npos ? command_ : command_.substr(0, sp));
            } catch (...) { msg.value = 0.0; }
            msg.unit = (sp == std::string::npos) ? "" : command_.substr(sp + 1);
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::NumberCommand>>(pub_)->publish(msg);

        } else if (t == "Player") {
            openhab_msgs::msg::PlayerCommand msg;
            msg.header = makeHeader(); msg.item_name = item_name_; msg.command = command_;
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::PlayerCommand>>(pub_)->publish(msg);

        } else if (t == "Rollershutter") {
            openhab_msgs::msg::RollershutterCommand msg;
            msg.header = makeHeader(); msg.item_name = item_name_; msg.command_type = command_;
            try { msg.percent = std::stof(command_); } catch (...) { msg.percent = 0.0f; }
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::RollershutterCommand>>(pub_)->publish(msg);

        } else {
            // String and any unknown type
            openhab_msgs::msg::StringCommand msg;
            msg.header = makeHeader(); msg.item_name = item_name_; msg.command = command_;
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::StringCommand>>(pub_)->publish(msg);
        }

        RCLCPP_INFO(get_logger(), "Published: %s <- %s", item_name_.c_str(), command_.c_str());
    }
};

int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<OpenHABPublisher>());
    rclcpp::shutdown();
    return 0;
}
