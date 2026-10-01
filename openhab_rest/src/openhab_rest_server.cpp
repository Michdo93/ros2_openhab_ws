/**
 * openhab_rest_server.cpp
 * =======================
 * ROS2 C++ service server that bridges openHAB REST API calls via libcurl.
 *
 * Advertises the same services as the Python counterpart:
 *   /openhab/get_state/{call,color,contact,datetime,dimmer,image,location,
 *                        number,player,rollershutter,string,switch}
 *   /openhab/send_command/{color,contact,datetime,dimmer,location,number,
 *                           player,rollershutter,string,switch}
 *
 * Parameters:
 *   openhab_url      (string, default: "http://127.0.0.1:8080")
 *   openhab_token    (string, default: "")
 *   openhab_user     (string, default: "openhab")
 *   openhab_password (string, default: "habopen")
 *
 * Build dependency: libcurl  (apt install libcurl4-openssl-dev)
 *
 * Usage:
 *   ros2 run openhab_rest openhab_rest_server_cpp \
 *       --ros-args -p openhab_url:=http://192.168.1.100:8080 \
 *                  -p openhab_token:=oh.openhab.xxxx
 */

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/header.hpp>
#include <curl/curl.h>

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


// ── libcurl write callback ────────────────────────────────────────────────────
static size_t curlWriteCallback(void* contents, size_t size, size_t nmemb, std::string* out) {
    out->append(static_cast<char*>(contents), size * nmemb);
    return size * nmemb;
}

// ── REST helper class ─────────────────────────────────────────────────────────
class OpenHABClient {
public:
    OpenHABClient(const std::string& base_url,
                  const std::string& token,
                  const std::string& user,
                  const std::string& password)
        : base_url_(base_url), token_(token), user_(user), password_(password) {
        curl_global_init(CURL_GLOBAL_DEFAULT);
    }

    ~OpenHABClient() { curl_global_cleanup(); }

    /** GET /rest/items/<name>/state  → raw state string */
    std::string getItemState(const std::string& item_name) {
        std::string url = base_url_ + "/rest/items/" + item_name + "/state";
        return httpGet(url);
    }

    /** POST /rest/items/<name>  body: command string, returns HTTP status */
    long sendCommand(const std::string& item_name, const std::string& command) {
        std::string url = base_url_ + "/rest/items/" + item_name;
        return httpPost(url, command);
    }

private:
    std::string base_url_;
    std::string token_;
    std::string user_;
    std::string password_;

    void applyAuth(CURL* curl) {
        if (!token_.empty()) {
            std::string auth_header = "Authorization: Bearer " + token_;
            struct curl_slist* headers = nullptr;
            headers = curl_slist_append(headers, auth_header.c_str());
            curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        } else if (!user_.empty()) {
            curl_easy_setopt(curl, CURLOPT_USERPWD,
                (user_ + ":" + password_).c_str());
        }
    }

    std::string httpGet(const std::string& url) {
        CURL* curl = curl_easy_init();
        std::string result;
        if (!curl) throw std::runtime_error("curl_easy_init failed");

        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, curlWriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &result);
        applyAuth(curl);

        CURLcode res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);
        if (res != CURLE_OK) {
            throw std::runtime_error(std::string("GET failed: ") + curl_easy_strerror(res));
        }
        return result;
    }

    long httpPost(const std::string& url, const std::string& body) {
        CURL* curl = curl_easy_init();
        if (!curl) throw std::runtime_error("curl_easy_init failed");

        struct curl_slist* headers = nullptr;
        headers = curl_slist_append(headers, "Content-Type: text/plain");

        if (!token_.empty()) {
            std::string auth = "Authorization: Bearer " + token_;
            headers = curl_slist_append(headers, auth.c_str());
        } else if (!user_.empty()) {
            curl_easy_setopt(curl, CURLOPT_USERPWD,
                (user_ + ":" + password_).c_str());
        }

        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, body.c_str());

        std::string resp;
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, curlWriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &resp);

        CURLcode res = curl_easy_perform(curl);
        long http_code = 0;
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);

        if (res != CURLE_OK) {
            throw std::runtime_error(std::string("POST failed: ") + curl_easy_strerror(res));
        }
        return http_code;
    }
};

// ── Helper: build header ──────────────────────────────────────────────────────
static std_msgs::msg::Header makeHeader(rclcpp::Node* node) {
    std_msgs::msg::Header h;
    h.stamp = node->get_clock()->now();
    h.frame_id = "";
    return h;
}

// ── Parse helpers ─────────────────────────────────────────────────────────────
static void parseColor(const std::string& raw, float& h, float& s, float& b) {
    h = s = b = 0.0f;
    try {
        size_t p1 = raw.find(',');
        size_t p2 = raw.find(',', p1 + 1);
        h = std::stof(raw.substr(0, p1));
        s = std::stof(raw.substr(p1 + 1, p2 - p1 - 1));
        b = std::stof(raw.substr(p2 + 1));
    } catch (...) {}
}

static void parseLocation(const std::string& raw, double& lat, double& lon, double& alt) {
    lat = lon = alt = 0.0;
    try {
        size_t p1 = raw.find(',');
        size_t p2 = raw.find(',', p1 + 1);
        lat = std::stod(raw.substr(0, p1));
        lon = std::stod(raw.substr(p1 + 1, p2 - p1 - 1));
        if (p2 != std::string::npos) alt = std::stod(raw.substr(p2 + 1));
    } catch (...) {}
}

static float safeFloat(const std::string& s) {
    if (s == "NULL" || s == "UNDEF" || s.empty()) return 0.0f;
    try { return std::stof(s); } catch (...) { return 0.0f; }
}

static double safeDouble(const std::string& s) {
    if (s == "NULL" || s == "UNDEF" || s.empty()) return 0.0;
    try { return std::stod(s); } catch (...) { return 0.0; }
}

// ── Main node ─────────────────────────────────────────────────────────────────
class OpenHABRestServer : public rclcpp::Node {
public:
    OpenHABRestServer() : Node("openhab_rest_server_cpp") {
        // Parameters
        this->declare_parameter("openhab_url",      "http://127.0.0.1:8080");
        this->declare_parameter("openhab_token",    "");
        this->declare_parameter("openhab_user",     "openhab");
        this->declare_parameter("openhab_password", "habopen");

        auto url  = this->get_parameter("openhab_url").as_string();
        auto tok  = this->get_parameter("openhab_token").as_string();
        auto usr  = this->get_parameter("openhab_user").as_string();
        auto pwd  = this->get_parameter("openhab_password").as_string();

        client_ = std::make_unique<OpenHABClient>(url, tok, usr, pwd);
        RCLCPP_INFO(this->get_logger(), "Connected to openHAB at %s", url.c_str());

        // GetState services
        using namespace std::placeholders;
        srv_get_call_   = create_service<openhab_msgs::srv::GetCallState>("/openhab/get_state/call",    std::bind(&OpenHABRestServer::getCallState, this, _1, _2));
        srv_get_color_  = create_service<openhab_msgs::srv::GetColorState>("/openhab/get_state/color",  std::bind(&OpenHABRestServer::getColorState, this, _1, _2));
        srv_get_contact_= create_service<openhab_msgs::srv::GetContactState>("/openhab/get_state/contact", std::bind(&OpenHABRestServer::getContactState, this, _1, _2));
        srv_get_dt_     = create_service<openhab_msgs::srv::GetDateTimeState>("/openhab/get_state/datetime", std::bind(&OpenHABRestServer::getDateTimeState, this, _1, _2));
        srv_get_dimmer_ = create_service<openhab_msgs::srv::GetDimmerState>("/openhab/get_state/dimmer",   std::bind(&OpenHABRestServer::getDimmerState, this, _1, _2));
        srv_get_image_  = create_service<openhab_msgs::srv::GetImageState>("/openhab/get_state/image",     std::bind(&OpenHABRestServer::getImageState, this, _1, _2));
        srv_get_loc_    = create_service<openhab_msgs::srv::GetLocationState>("/openhab/get_state/location", std::bind(&OpenHABRestServer::getLocationState, this, _1, _2));
        srv_get_num_    = create_service<openhab_msgs::srv::GetNumberState>("/openhab/get_state/number",    std::bind(&OpenHABRestServer::getNumberState, this, _1, _2));
        srv_get_player_ = create_service<openhab_msgs::srv::GetPlayerState>("/openhab/get_state/player",   std::bind(&OpenHABRestServer::getPlayerState, this, _1, _2));
        srv_get_roller_ = create_service<openhab_msgs::srv::GetRollershutterState>("/openhab/get_state/rollershutter", std::bind(&OpenHABRestServer::getRollerState, this, _1, _2));
        srv_get_str_    = create_service<openhab_msgs::srv::GetStringState>("/openhab/get_state/string",   std::bind(&OpenHABRestServer::getStringState, this, _1, _2));
        srv_get_sw_     = create_service<openhab_msgs::srv::GetSwitchState>("/openhab/get_state/switch",   std::bind(&OpenHABRestServer::getSwitchState, this, _1, _2));

        // SendCommand services
        srv_cmd_color_  = create_service<openhab_msgs::srv::SendColorCommand>("/openhab/send_command/color",    std::bind(&OpenHABRestServer::sendCmd<openhab_msgs::srv::SendColorCommand>, this, _1, _2));
        srv_cmd_contact_= create_service<openhab_msgs::srv::SendContactCommand>("/openhab/send_command/contact", std::bind(&OpenHABRestServer::sendCmd<openhab_msgs::srv::SendContactCommand>, this, _1, _2));
        srv_cmd_dt_     = create_service<openhab_msgs::srv::SendDateTimeCommand>("/openhab/send_command/datetime", std::bind(&OpenHABRestServer::sendCmd<openhab_msgs::srv::SendDateTimeCommand>, this, _1, _2));
        srv_cmd_dimmer_ = create_service<openhab_msgs::srv::SendDimmerCommand>("/openhab/send_command/dimmer",   std::bind(&OpenHABRestServer::sendCmd<openhab_msgs::srv::SendDimmerCommand>, this, _1, _2));
        srv_cmd_loc_    = create_service<openhab_msgs::srv::SendLocationCommand>("/openhab/send_command/location", std::bind(&OpenHABRestServer::sendCmd<openhab_msgs::srv::SendLocationCommand>, this, _1, _2));
        srv_cmd_num_    = create_service<openhab_msgs::srv::SendNumberCommand>("/openhab/send_command/number",   std::bind(&OpenHABRestServer::sendCmd<openhab_msgs::srv::SendNumberCommand>, this, _1, _2));
        srv_cmd_player_ = create_service<openhab_msgs::srv::SendPlayerCommand>("/openhab/send_command/player",  std::bind(&OpenHABRestServer::sendCmd<openhab_msgs::srv::SendPlayerCommand>, this, _1, _2));
        srv_cmd_roller_ = create_service<openhab_msgs::srv::SendRollershutterCommand>("/openhab/send_command/rollershutter", std::bind(&OpenHABRestServer::sendCmd<openhab_msgs::srv::SendRollershutterCommand>, this, _1, _2));
        srv_cmd_str_    = create_service<openhab_msgs::srv::SendStringCommand>("/openhab/send_command/string",   std::bind(&OpenHABRestServer::sendCmd<openhab_msgs::srv::SendStringCommand>, this, _1, _2));
        srv_cmd_sw_     = create_service<openhab_msgs::srv::SendSwitchCommand>("/openhab/send_command/switch",   std::bind(&OpenHABRestServer::sendCmd<openhab_msgs::srv::SendSwitchCommand>, this, _1, _2));

        RCLCPP_INFO(this->get_logger(), "All GetState and SendCommand services ready.");
    }

private:
    std::unique_ptr<OpenHABClient> client_;

    // GetState service handles
    rclcpp::Service<openhab_msgs::srv::GetCallState>::SharedPtr          srv_get_call_;
    rclcpp::Service<openhab_msgs::srv::GetColorState>::SharedPtr         srv_get_color_;
    rclcpp::Service<openhab_msgs::srv::GetContactState>::SharedPtr       srv_get_contact_;
    rclcpp::Service<openhab_msgs::srv::GetDateTimeState>::SharedPtr      srv_get_dt_;
    rclcpp::Service<openhab_msgs::srv::GetDimmerState>::SharedPtr        srv_get_dimmer_;
    rclcpp::Service<openhab_msgs::srv::GetImageState>::SharedPtr         srv_get_image_;
    rclcpp::Service<openhab_msgs::srv::GetLocationState>::SharedPtr      srv_get_loc_;
    rclcpp::Service<openhab_msgs::srv::GetNumberState>::SharedPtr        srv_get_num_;
    rclcpp::Service<openhab_msgs::srv::GetPlayerState>::SharedPtr        srv_get_player_;
    rclcpp::Service<openhab_msgs::srv::GetRollershutterState>::SharedPtr srv_get_roller_;
    rclcpp::Service<openhab_msgs::srv::GetStringState>::SharedPtr        srv_get_str_;
    rclcpp::Service<openhab_msgs::srv::GetSwitchState>::SharedPtr        srv_get_sw_;
    // SendCommand service handles
    rclcpp::Service<openhab_msgs::srv::SendColorCommand>::SharedPtr         srv_cmd_color_;
    rclcpp::Service<openhab_msgs::srv::SendContactCommand>::SharedPtr       srv_cmd_contact_;
    rclcpp::Service<openhab_msgs::srv::SendDateTimeCommand>::SharedPtr      srv_cmd_dt_;
    rclcpp::Service<openhab_msgs::srv::SendDimmerCommand>::SharedPtr        srv_cmd_dimmer_;
    rclcpp::Service<openhab_msgs::srv::SendLocationCommand>::SharedPtr      srv_cmd_loc_;
    rclcpp::Service<openhab_msgs::srv::SendNumberCommand>::SharedPtr        srv_cmd_num_;
    rclcpp::Service<openhab_msgs::srv::SendPlayerCommand>::SharedPtr        srv_cmd_player_;
    rclcpp::Service<openhab_msgs::srv::SendRollershutterCommand>::SharedPtr srv_cmd_roller_;
    rclcpp::Service<openhab_msgs::srv::SendStringCommand>::SharedPtr        srv_cmd_str_;
    rclcpp::Service<openhab_msgs::srv::SendSwitchCommand>::SharedPtr        srv_cmd_sw_;

    // ── Generic SendCommand handler (works for all command service types) ──
    template<typename SrvT>
    void sendCmd(const typename SrvT::Request::SharedPtr req,
                 const typename SrvT::Response::SharedPtr res) {
        try {
            long code = client_->sendCommand(req->item_name, req->command);
            res->success = (code >= 200 && code < 300);
            res->message = "HTTP " + std::to_string(code);
        } catch (const std::exception& e) {
            res->success = false;
            res->message = e.what();
        }
    }

    // ── GetState handlers ──────────────────────────────────────────────────
    void getCallState(const openhab_msgs::srv::GetCallState::Request::SharedPtr req,
                      const openhab_msgs::srv::GetCallState::Response::SharedPtr res) {
        try {
            auto raw = client_->getItemState(req->item_name);
            res->state.header = makeHeader(this);
            res->state.item_name = req->item_name;
            res->state.state = raw;
            res->success = true;
        } catch (const std::exception& e) { res->success = false; res->message = e.what(); }
    }

    void getColorState(const openhab_msgs::srv::GetColorState::Request::SharedPtr req,
                       const openhab_msgs::srv::GetColorState::Response::SharedPtr res) {
        try {
            auto raw = client_->getItemState(req->item_name);
            float h, s, b;
            parseColor(raw, h, s, b);
            res->state.header = makeHeader(this);
            res->state.item_name = req->item_name;
            res->state.hue = h; res->state.saturation = s; res->state.brightness = b;
            res->state.state = raw;
            res->success = true;
        } catch (const std::exception& e) { res->success = false; res->message = e.what(); }
    }

    void getContactState(const openhab_msgs::srv::GetContactState::Request::SharedPtr req,
                         const openhab_msgs::srv::GetContactState::Response::SharedPtr res) {
        try {
            auto raw = client_->getItemState(req->item_name);
            res->state.header = makeHeader(this); res->state.item_name = req->item_name; res->state.state = raw;
            res->success = true;
        } catch (const std::exception& e) { res->success = false; res->message = e.what(); }
    }

    void getDateTimeState(const openhab_msgs::srv::GetDateTimeState::Request::SharedPtr req,
                          const openhab_msgs::srv::GetDateTimeState::Response::SharedPtr res) {
        try {
            auto raw = client_->getItemState(req->item_name);
            res->state.header = makeHeader(this); res->state.item_name = req->item_name; res->state.state = raw;
            res->success = true;
        } catch (const std::exception& e) { res->success = false; res->message = e.what(); }
    }

    void getDimmerState(const openhab_msgs::srv::GetDimmerState::Request::SharedPtr req,
                        const openhab_msgs::srv::GetDimmerState::Response::SharedPtr res) {
        try {
            auto raw = client_->getItemState(req->item_name);
            res->state.header = makeHeader(this); res->state.item_name = req->item_name;
            res->state.state = safeFloat(raw);
            res->success = true;
        } catch (const std::exception& e) { res->success = false; res->message = e.what(); }
    }

    void getImageState(const openhab_msgs::srv::GetImageState::Request::SharedPtr req,
                       const openhab_msgs::srv::GetImageState::Response::SharedPtr res) {
        try {
            auto raw = client_->getItemState(req->item_name);
            res->state.header = makeHeader(this); res->state.item_name = req->item_name; res->state.state = raw;
            res->success = true;
        } catch (const std::exception& e) { res->success = false; res->message = e.what(); }
    }

    void getLocationState(const openhab_msgs::srv::GetLocationState::Request::SharedPtr req,
                          const openhab_msgs::srv::GetLocationState::Response::SharedPtr res) {
        try {
            auto raw = client_->getItemState(req->item_name);
            double lat, lon, alt;
            parseLocation(raw, lat, lon, alt);
            res->state.header = makeHeader(this); res->state.item_name = req->item_name;
            res->state.latitude = lat; res->state.longitude = lon; res->state.altitude = alt;
            res->state.state = raw;
            res->success = true;
        } catch (const std::exception& e) { res->success = false; res->message = e.what(); }
    }

    void getNumberState(const openhab_msgs::srv::GetNumberState::Request::SharedPtr req,
                        const openhab_msgs::srv::GetNumberState::Response::SharedPtr res) {
        try {
            auto raw = client_->getItemState(req->item_name);
            auto sp = raw.find(' ');
            std::string num_s = (sp == std::string::npos) ? raw : raw.substr(0, sp);
            std::string unit  = (sp == std::string::npos) ? "" : raw.substr(sp + 1);
            res->state.header = makeHeader(this); res->state.item_name = req->item_name;
            res->state.state = safeDouble(num_s); res->state.unit = unit;
            res->success = true;
        } catch (const std::exception& e) { res->success = false; res->message = e.what(); }
    }

    void getPlayerState(const openhab_msgs::srv::GetPlayerState::Request::SharedPtr req,
                        const openhab_msgs::srv::GetPlayerState::Response::SharedPtr res) {
        try {
            auto raw = client_->getItemState(req->item_name);
            res->state.header = makeHeader(this); res->state.item_name = req->item_name; res->state.state = raw;
            res->success = true;
        } catch (const std::exception& e) { res->success = false; res->message = e.what(); }
    }

    void getRollerState(const openhab_msgs::srv::GetRollershutterState::Request::SharedPtr req,
                        const openhab_msgs::srv::GetRollershutterState::Response::SharedPtr res) {
        try {
            auto raw = client_->getItemState(req->item_name);
            res->state.header = makeHeader(this); res->state.item_name = req->item_name;
            res->state.state = safeFloat(raw);
            res->success = true;
        } catch (const std::exception& e) { res->success = false; res->message = e.what(); }
    }

    void getStringState(const openhab_msgs::srv::GetStringState::Request::SharedPtr req,
                        const openhab_msgs::srv::GetStringState::Response::SharedPtr res) {
        try {
            auto raw = client_->getItemState(req->item_name);
            res->state.header = makeHeader(this); res->state.item_name = req->item_name; res->state.state = raw;
            res->success = true;
        } catch (const std::exception& e) { res->success = false; res->message = e.what(); }
    }

    void getSwitchState(const openhab_msgs::srv::GetSwitchState::Request::SharedPtr req,
                        const openhab_msgs::srv::GetSwitchState::Response::SharedPtr res) {
        try {
            auto raw = client_->getItemState(req->item_name);
            res->state.header = makeHeader(this); res->state.item_name = req->item_name; res->state.state = raw;
            res->success = true;
        } catch (const std::exception& e) { res->success = false; res->message = e.what(); }
    }
};

// ── main ──────────────────────────────────────────────────────────────────────
int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<OpenHABRestServer>());
    rclcpp::shutdown();
    return 0;
}
