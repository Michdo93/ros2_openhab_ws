/**
 * openhab_event_publisher.cpp
 * ===========================
 * ROS2 C++ node that streams openHAB ItemStateChangedEvents via SSE
 * (Server-Sent Events using libcurl) and publishes typed state messages.
 *
 * Topic schema:  /openhab/state/<ItemName>
 *
 * Parameters:
 *   openhab_url      (string)  default: "http://127.0.0.1:8080"
 *   openhab_token    (string)  default: ""
 *   openhab_user     (string)  default: "openhab"
 *   openhab_password (string)  default: "habopen"
 *   item_type_map    (string)  default: ""
 *     JSON dict e.g. '{"LivingRoomLight":"Switch","Dimmer1":"Dimmer"}'
 *
 * Build deps: libcurl4-openssl-dev, nlohmann-json3-dev
 */

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/header.hpp>
#include <curl/curl.h>
#include <nlohmann/json.hpp>

#include <thread>
#include <atomic>
#include <sstream>
#include <unordered_map>

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

using json = nlohmann::json;

// ─────────────────────────────────────────────────────────────────────────────
// SSE line buffer: libcurl calls this for each received chunk.
// We accumulate chunks into lines manually.
// ─────────────────────────────────────────────────────────────────────────────
struct SSEContext {
    std::function<void(const std::string&)> lineCallback;
    std::string buffer;
};

static size_t sseWriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    size_t total = size * nmemb;
    auto* ctx = static_cast<SSEContext*>(userp);
    ctx->buffer.append(static_cast<char*>(contents), total);

    // Process complete lines
    size_t pos;
    while ((pos = ctx->buffer.find('\n')) != std::string::npos) {
        std::string line = ctx->buffer.substr(0, pos);
        // Strip trailing \r
        if (!line.empty() && line.back() == '\r') line.pop_back();
        ctx->lineCallback(line);
        ctx->buffer.erase(0, pos + 1);
    }
    return total;
}

// ─────────────────────────────────────────────────────────────────────────────
class OpenHABEventPublisher : public rclcpp::Node {
public:
    OpenHABEventPublisher() : Node("openhab_event_publisher_cpp"), running_(true) {
        declare_parameter("openhab_url",      "http://127.0.0.1:8080");
        declare_parameter("openhab_token",    "");
        declare_parameter("openhab_user",     "openhab");
        declare_parameter("openhab_password", "habopen");
        declare_parameter("item_type_map",    "");
        declare_parameter("queue_size",       10);

        url_      = get_parameter("openhab_url").as_string();
        token_    = get_parameter("openhab_token").as_string();
        user_     = get_parameter("openhab_user").as_string();
        password_ = get_parameter("openhab_password").as_string();
        int qsize = get_parameter("queue_size").as_int();
        qsize_    = static_cast<size_t>(qsize);

        // Parse item type map
        auto map_json = get_parameter("item_type_map").as_string();
        if (!map_json.empty()) {
            try {
                auto j = json::parse(map_json);
                for (auto& [k, v] : j.items()) {
                    item_type_map_[k] = v.get<std::string>();
                }
                RCLCPP_INFO(get_logger(), "Item type map: %zu entries", item_type_map_.size());
            } catch (const std::exception& e) {
                RCLCPP_ERROR(get_logger(), "item_type_map parse error: %s", e.what());
            }
        }

        curl_global_init(CURL_GLOBAL_DEFAULT);
        RCLCPP_INFO(get_logger(), "Listening for ItemStateChangedEvents from %s", url_.c_str());

        sse_thread_ = std::thread(&OpenHABEventPublisher::sseLoop, this);
    }

    ~OpenHABEventPublisher() {
        running_ = false;
        if (sse_thread_.joinable()) sse_thread_.join();
        curl_global_cleanup();
    }

private:
    std::string url_, token_, user_, password_;
    size_t qsize_;
    std::atomic<bool> running_;
    std::thread sse_thread_;
    std::unordered_map<std::string, std::string> item_type_map_;

    // Publisher cache – stores type-erased shared_ptr
    // We use std::any or a variant; for simplicity we store per-type maps
    std::unordered_map<std::string, rclcpp::PublisherBase::SharedPtr> publishers_;

    // ── Helper: make header ────────────────────────────────────────────────
    std_msgs::msg::Header makeHeader() {
        std_msgs::msg::Header h;
        h.stamp = get_clock()->now();
        h.frame_id = "";
        return h;
    }

    // ── Helper: parse color ────────────────────────────────────────────────
    void parseColor(const std::string& raw, float& h, float& s, float& b) {
        h = s = b = 0.0f;
        try {
            auto p1 = raw.find(',');
            auto p2 = raw.find(',', p1 + 1);
            h = std::stof(raw.substr(0, p1));
            s = std::stof(raw.substr(p1 + 1, p2 - p1 - 1));
            b = std::stof(raw.substr(p2 + 1));
        } catch (...) {}
    }

    // ── Helper: parse location ─────────────────────────────────────────────
    void parseLocation(const std::string& raw, double& lat, double& lon, double& alt) {
        lat = lon = alt = 0.0;
        try {
            auto p1 = raw.find(',');
            auto p2 = raw.find(',', p1 + 1);
            lat = std::stod(raw.substr(0, p1));
            lon = std::stod(raw.substr(p1 + 1, p2 - p1 - 1));
            if (p2 != std::string::npos) alt = std::stod(raw.substr(p2 + 1));
        } catch (...) {}
    }

    // ── Publish a message for a given item ────────────────────────────────
    void publishState(const std::string& item_name,
                      const std::string& item_type,
                      const std::string& value) {
        std::string topic = "/openhab/state/" + item_name;

        if (item_type == "Switch") {
            auto& pub = getOrCreatePub<openhab_msgs::msg::SwitchState>(item_name, topic);
            openhab_msgs::msg::SwitchState msg;
            msg.header = makeHeader(); msg.item_name = item_name; msg.state = value;
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::SwitchState>>(pub)->publish(msg);
        }
        else if (item_type == "Dimmer") {
            auto& pub = getOrCreatePub<openhab_msgs::msg::DimmerState>(item_name, topic);
            openhab_msgs::msg::DimmerState msg;
            msg.header = makeHeader(); msg.item_name = item_name;
            try { msg.state = std::stof(value); } catch (...) { msg.state = 0.0f; }
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::DimmerState>>(pub)->publish(msg);
        }
        else if (item_type == "Color") {
            auto& pub = getOrCreatePub<openhab_msgs::msg::ColorState>(item_name, topic);
            openhab_msgs::msg::ColorState msg;
            float h, s, b;
            parseColor(value, h, s, b);
            msg.header = makeHeader(); msg.item_name = item_name;
            msg.hue = h; msg.saturation = s; msg.brightness = b; msg.state = value;
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::ColorState>>(pub)->publish(msg);
        }
        else if (item_type == "Contact") {
            auto& pub = getOrCreatePub<openhab_msgs::msg::ContactState>(item_name, topic);
            openhab_msgs::msg::ContactState msg;
            msg.header = makeHeader(); msg.item_name = item_name; msg.state = value;
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::ContactState>>(pub)->publish(msg);
        }
        else if (item_type == "DateTime") {
            auto& pub = getOrCreatePub<openhab_msgs::msg::DateTimeState>(item_name, topic);
            openhab_msgs::msg::DateTimeState msg;
            msg.header = makeHeader(); msg.item_name = item_name; msg.state = value;
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::DateTimeState>>(pub)->publish(msg);
        }
        else if (item_type == "Location") {
            auto& pub = getOrCreatePub<openhab_msgs::msg::LocationState>(item_name, topic);
            double lat, lon, alt;
            parseLocation(value, lat, lon, alt);
            openhab_msgs::msg::LocationState msg;
            msg.header = makeHeader(); msg.item_name = item_name;
            msg.latitude = lat; msg.longitude = lon; msg.altitude = alt; msg.state = value;
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::LocationState>>(pub)->publish(msg);
        }
        else if (item_type == "Number" || item_type.rfind("Number:", 0) == 0) {
            auto& pub = getOrCreatePub<openhab_msgs::msg::NumberState>(item_name, topic);
            openhab_msgs::msg::NumberState msg;
            auto sp = value.find(' ');
            std::string num_s = (sp == std::string::npos) ? value : value.substr(0, sp);
            std::string unit  = (sp == std::string::npos) ? "" : value.substr(sp + 1);
            msg.header = makeHeader(); msg.item_name = item_name;
            try { msg.state = std::stod(num_s); } catch (...) { msg.state = 0.0; }
            msg.unit = unit;
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::NumberState>>(pub)->publish(msg);
        }
        else if (item_type == "Player") {
            auto& pub = getOrCreatePub<openhab_msgs::msg::PlayerState>(item_name, topic);
            openhab_msgs::msg::PlayerState msg;
            msg.header = makeHeader(); msg.item_name = item_name; msg.state = value;
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::PlayerState>>(pub)->publish(msg);
        }
        else if (item_type == "Rollershutter") {
            auto& pub = getOrCreatePub<openhab_msgs::msg::RollershutterState>(item_name, topic);
            openhab_msgs::msg::RollershutterState msg;
            msg.header = makeHeader(); msg.item_name = item_name;
            try { msg.state = std::stof(value); } catch (...) { msg.state = 0.0f; }
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::RollershutterState>>(pub)->publish(msg);
        }
        else if (item_type == "Call") {
            auto& pub = getOrCreatePub<openhab_msgs::msg::CallState>(item_name, topic);
            openhab_msgs::msg::CallState msg;
            msg.header = makeHeader(); msg.item_name = item_name; msg.state = value;
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::CallState>>(pub)->publish(msg);
        }
        else {
            // Fallback: StringState
            auto& pub = getOrCreatePub<openhab_msgs::msg::StringState>(item_name, topic);
            openhab_msgs::msg::StringState msg;
            msg.header = makeHeader(); msg.item_name = item_name; msg.state = value;
            std::static_pointer_cast<rclcpp::Publisher<openhab_msgs::msg::StringState>>(pub)->publish(msg);
        }

        RCLCPP_DEBUG(get_logger(), "Published %s = %s", item_name.c_str(), value.c_str());
    }

    template<typename MsgT>
    rclcpp::PublisherBase::SharedPtr& getOrCreatePub(const std::string& item_name,
                                                      const std::string& topic) {
        auto it = publishers_.find(item_name);
        if (it == publishers_.end()) {
            auto pub = create_publisher<MsgT>(topic, qsize_);
            RCLCPP_INFO(get_logger(), "Created publisher: %s", topic.c_str());
            publishers_[item_name] = pub;
        }
        return publishers_[item_name];
    }

    // ── SSE processing ─────────────────────────────────────────────────────
    void processSSELine(const std::string& line) {
        // SSE format: "data: <json>"
        if (line.rfind("data: ", 0) != 0) return;
        std::string json_str = line.substr(6);
        try {
            auto data = json::parse(json_str);
            if (data.value("type", "") != "ItemStateChangedEvent") return;

            std::string topic_str = data.value("topic", "");
            // topic: "openhab/items/<ItemName>/statechanged"
            std::istringstream ss(topic_str);
            std::vector<std::string> parts;
            std::string part;
            while (std::getline(ss, part, '/')) parts.push_back(part);
            if (parts.size() < 3) return;
            std::string item_name = parts[2];

            auto payload = json::parse(data.value("payload", "{}"));
            std::string value = payload.value("value", "");

            std::string item_type = "String";
            auto it = item_type_map_.find(item_name);
            if (it != item_type_map_.end()) item_type = it->second;

            publishState(item_name, item_type, value);

        } catch (const std::exception& e) {
            RCLCPP_WARN(get_logger(), "SSE parse error: %s", e.what());
        }
    }

    // ── SSE background thread ──────────────────────────────────────────────
    void sseLoop() {
        std::string sse_url = url_ + "/rest/events?topics=openhab/items/*/statechanged";

        SSEContext ctx;
        ctx.lineCallback = [this](const std::string& line) {
            if (rclcpp::ok()) processSSELine(line);
        };

        while (running_ && rclcpp::ok()) {
            CURL* curl = curl_easy_init();
            if (!curl) {
                RCLCPP_ERROR(get_logger(), "curl_easy_init failed");
                std::this_thread::sleep_for(std::chrono::seconds(5));
                continue;
            }

            struct curl_slist* headers = nullptr;
            headers = curl_slist_append(headers, "Accept: text/event-stream");
            headers = curl_slist_append(headers, "Cache-Control: no-cache");

            if (!token_.empty()) {
                std::string auth = "Authorization: Bearer " + token_;
                headers = curl_slist_append(headers, auth.c_str());
            } else if (!user_.empty()) {
                curl_easy_setopt(curl, CURLOPT_USERPWD,
                    (user_ + ":" + password_).c_str());
            }

            curl_easy_setopt(curl, CURLOPT_URL, sse_url.c_str());
            curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, sseWriteCallback);
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, &ctx);
            curl_easy_setopt(curl, CURLOPT_TIMEOUT, 0L);   // no timeout
            curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT, 10L);

            CURLcode res = curl_easy_perform(curl);
            if (res != CURLE_OK && running_) {
                RCLCPP_WARN(get_logger(), "SSE connection lost: %s – reconnecting in 5s",
                    curl_easy_strerror(res));
            }

            curl_slist_free_all(headers);
            curl_easy_cleanup(curl);

            if (running_) {
                std::this_thread::sleep_for(std::chrono::seconds(5));
            }
        }
    }
};

int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<OpenHABEventPublisher>());
    rclcpp::shutdown();
    return 0;
}
