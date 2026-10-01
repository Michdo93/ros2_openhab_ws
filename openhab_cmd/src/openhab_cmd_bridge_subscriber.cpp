/**
 * openhab_cmd_bridge_subscriber.cpp
 * ==================================
 * C++ bridge subscriber: subscribes to /openhab/command/<item_name>
 * and forwards each received command to the openHAB REST API via libcurl.
 *
 * Parameters:
 *   item_name        (string, required)
 *   item_type        (string, default: "Switch")
 *   openhab_url      (string, default: "http://127.0.0.1:8080")
 *   openhab_token    (string, default: "")
 *   openhab_user     (string, default: "openhab")
 *   openhab_password (string, default: "habopen")
 *
 * Build deps: libcurl4-openssl-dev
 *
 * Usage:
 *   ros2 run openhab_cmd openhab_cmd_bridge_subscriber_cpp \
 *       --ros-args -p item_name:=LivingRoomLight \
 *                  -p item_type:=Switch \
 *                  -p openhab_url:=http://192.168.1.100:8080 \
 *                  -p openhab_token:=oh.openhab.xxxx
 */

#include <rclcpp/rclcpp.hpp>
#include <curl/curl.h>
#include <string>
#include <memory>
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

static size_t dummyWrite(void*, size_t s, size_t n, void*) { return s * n; }

class OpenHABCmdBridgeSubscriber : public rclcpp::Node {
public:
    OpenHABCmdBridgeSubscriber() : Node("openhab_cmd_bridge_subscriber_cpp") {
        declare_parameter("item_name",        "");
        declare_parameter("item_type",        "Switch");
        declare_parameter("openhab_url",      "http://127.0.0.1:8080");
        declare_parameter("openhab_token",    "");
        declare_parameter("openhab_user",     "openhab");
        declare_parameter("openhab_password", "habopen");

        item_name_ = get_parameter("item_name").as_string();
        item_type_ = get_parameter("item_type").as_string();
        url_       = get_parameter("openhab_url").as_string();
        token_     = get_parameter("openhab_token").as_string();
        user_      = get_parameter("openhab_user").as_string();
        password_  = get_parameter("openhab_password").as_string();

        if (item_name_.empty()) { RCLCPP_ERROR(get_logger(), "'item_name' required!"); return; }

        curl_global_init(CURL_GLOBAL_DEFAULT);

        std::string topic = "/openhab/command/" + item_name_;
        RCLCPP_INFO(get_logger(), "Bridge: %s -> openHAB REST [%s]",
            topic.c_str(), item_type_.c_str());

        setupSubscription(topic);
    }

    ~OpenHABCmdBridgeSubscriber() { curl_global_cleanup(); }

private:
    std::string item_name_, item_type_, url_, token_, user_, password_;
    rclcpp::SubscriptionBase::SharedPtr sub_;

    void sendToOpenHAB(const std::string& item, const std::string& command) {
        std::string rest_url = url_ + "/rest/items/" + item;
        CURL* curl = curl_easy_init();
        if (!curl) { RCLCPP_ERROR(get_logger(), "curl_easy_init failed"); return; }

        struct curl_slist* headers = nullptr;
        headers = curl_slist_append(headers, "Content-Type: text/plain");
        if (!token_.empty()) {
            std::string auth = "Authorization: Bearer " + token_;
            headers = curl_slist_append(headers, auth.c_str());
        } else if (!user_.empty()) {
            curl_easy_setopt(curl, CURLOPT_USERPWD, (user_ + ":" + password_).c_str());
        }
        curl_easy_setopt(curl, CURLOPT_URL, rest_url.c_str());
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, command.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, dummyWrite);

        CURLcode res = curl_easy_perform(curl);
        long code = 0; curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &code);
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);

        if (res == CURLE_OK && code >= 200 && code < 300)
            RCLCPP_INFO(get_logger(), "Sent '%s' -> '%s' (HTTP %ld)", command.c_str(), item.c_str(), code);
        else
            RCLCPP_ERROR(get_logger(), "Failed '%s' -> '%s': %s (HTTP %ld)",
                command.c_str(), item.c_str(), curl_easy_strerror(res), code);
    }

    // Extract command string from message
    std::string extractCommand(const std::string& item_type, const openhab_msgs::msg::SwitchCommand& msg) { return msg.command; }
    std::string extractCommand(const std::string& item_type, const openhab_msgs::msg::DimmerCommand& msg) {
        if (!msg.command_type.empty() && msg.command_type != "0") return msg.command_type;
        std::ostringstream ss; ss << msg.percent; return ss.str();
    }
    std::string extractCommand(const std::string& item_type, const openhab_msgs::msg::ColorCommand& msg) {
        if (msg.command_type == "ON" || msg.command_type == "OFF" ||
            msg.command_type == "INCREASE" || msg.command_type == "DECREASE" ||
            msg.command_type == "REFRESH") return msg.command_type;
        std::ostringstream ss;
        ss << msg.hue << "," << msg.saturation << "," << msg.brightness; return ss.str();
    }
    std::string extractCommand(const std::string& item_type, const openhab_msgs::msg::ContactCommand& msg) { return msg.command; }
    std::string extractCommand(const std::string& item_type, const openhab_msgs::msg::DateTimeCommand& msg) { return msg.command; }
    std::string extractCommand(const std::string& item_type, const openhab_msgs::msg::LocationCommand& msg) {
        std::ostringstream ss;
        ss << msg.latitude << "," << msg.longitude << "," << msg.altitude; return ss.str();
    }
    std::string extractCommand(const std::string& item_type, const openhab_msgs::msg::NumberCommand& msg) {
        std::ostringstream ss; ss << msg.value;
        if (!msg.unit.empty()) ss << " " << msg.unit; return ss.str();
    }
    std::string extractCommand(const std::string& item_type, const openhab_msgs::msg::PlayerCommand& msg) { return msg.command; }
    std::string extractCommand(const std::string& item_type, const openhab_msgs::msg::RollershutterCommand& msg) {
        if (msg.command_type == "UP" || msg.command_type == "DOWN" ||
            msg.command_type == "STOP" || msg.command_type == "MOVE" ||
            msg.command_type == "REFRESH") return msg.command_type;
        std::ostringstream ss; ss << msg.percent; return ss.str();
    }
    std::string extractCommand(const std::string& item_type, const openhab_msgs::msg::StringCommand& msg) { return msg.command; }

    void setupSubscription(const std::string& topic) {
        if (item_type_ == "Switch") {
            sub_ = create_subscription<openhab_msgs::msg::SwitchCommand>(topic, 10,
                [this](openhab_msgs::msg::SwitchCommand::SharedPtr msg) {
                    sendToOpenHAB(msg->item_name, extractCommand(item_type_, *msg));
                });
        } else if (item_type_ == "Dimmer") {
            sub_ = create_subscription<openhab_msgs::msg::DimmerCommand>(topic, 10,
                [this](openhab_msgs::msg::DimmerCommand::SharedPtr msg) {
                    sendToOpenHAB(msg->item_name, extractCommand(item_type_, *msg));
                });
        } else if (item_type_ == "Color") {
            sub_ = create_subscription<openhab_msgs::msg::ColorCommand>(topic, 10,
                [this](openhab_msgs::msg::ColorCommand::SharedPtr msg) {
                    sendToOpenHAB(msg->item_name, extractCommand(item_type_, *msg));
                });
        } else if (item_type_ == "Contact") {
            sub_ = create_subscription<openhab_msgs::msg::ContactCommand>(topic, 10,
                [this](openhab_msgs::msg::ContactCommand::SharedPtr msg) {
                    sendToOpenHAB(msg->item_name, extractCommand(item_type_, *msg));
                });
        } else if (item_type_ == "DateTime") {
            sub_ = create_subscription<openhab_msgs::msg::DateTimeCommand>(topic, 10,
                [this](openhab_msgs::msg::DateTimeCommand::SharedPtr msg) {
                    sendToOpenHAB(msg->item_name, extractCommand(item_type_, *msg));
                });
        } else if (item_type_ == "Location") {
            sub_ = create_subscription<openhab_msgs::msg::LocationCommand>(topic, 10,
                [this](openhab_msgs::msg::LocationCommand::SharedPtr msg) {
                    sendToOpenHAB(msg->item_name, extractCommand(item_type_, *msg));
                });
        } else if (item_type_ == "Number") {
            sub_ = create_subscription<openhab_msgs::msg::NumberCommand>(topic, 10,
                [this](openhab_msgs::msg::NumberCommand::SharedPtr msg) {
                    sendToOpenHAB(msg->item_name, extractCommand(item_type_, *msg));
                });
        } else if (item_type_ == "Player") {
            sub_ = create_subscription<openhab_msgs::msg::PlayerCommand>(topic, 10,
                [this](openhab_msgs::msg::PlayerCommand::SharedPtr msg) {
                    sendToOpenHAB(msg->item_name, extractCommand(item_type_, *msg));
                });
        } else if (item_type_ == "Rollershutter") {
            sub_ = create_subscription<openhab_msgs::msg::RollershutterCommand>(topic, 10,
                [this](openhab_msgs::msg::RollershutterCommand::SharedPtr msg) {
                    sendToOpenHAB(msg->item_name, extractCommand(item_type_, *msg));
                });
        } else if (item_type_ == "Contact") {
            sub_ = create_subscription<openhab_msgs::msg::ContactCommand>(topic, 10,
                [this](openhab_msgs::msg::ContactCommand::SharedPtr msg) {
                    sendToOpenHAB(msg->item_name, extractCommand(item_type_, *msg));
                });
        } else if (item_type_ == "DateTime") {
            sub_ = create_subscription<openhab_msgs::msg::DateTimeCommand>(topic, 10,
                [this](openhab_msgs::msg::DateTimeCommand::SharedPtr msg) {
                    sendToOpenHAB(msg->item_name, extractCommand(item_type_, *msg));
                });
        } else if (item_type_ == "Player") {
            sub_ = create_subscription<openhab_msgs::msg::PlayerCommand>(topic, 10,
                [this](openhab_msgs::msg::PlayerCommand::SharedPtr msg) {
                    sendToOpenHAB(msg->item_name, extractCommand(item_type_, *msg));
                });
        } else {
            // String fallback
            sub_ = create_subscription<openhab_msgs::msg::StringCommand>(topic, 10,
                [this](openhab_msgs::msg::StringCommand::SharedPtr msg) {
                    sendToOpenHAB(msg->item_name, extractCommand(item_type_, *msg));
                });
        }
    }
};

int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<OpenHABCmdBridgeSubscriber>());
    rclcpp::shutdown();
    return 0;
}
