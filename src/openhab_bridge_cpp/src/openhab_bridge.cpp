// openhab_bridge (C++) – same topics and services as the Python bridge:
//   /openhab/items/<Item>/state    openhab_msgs/ItemState  (transient local)
//   /openhab/items/<Item>/value    std_msgs/Float64        (numeric items)
//   /openhab/items/<Item>/command  std_msgs/String  -> command to openHAB
//   /openhab/command               openhab_msgs/ItemCommand
//   /openhab/get_item, /openhab/send_command, /openhab/list_items, /diagnostics
// Address and token come from OPENHAB_URL and OPENHAB_TOKEN (environment).
#include <openhab/openhab.hpp>

#include <atomic>
#include <chrono>
#include <cstdlib>
#include <ctime>
#include <diagnostic_msgs/msg/diagnostic_array.hpp>
#include <iomanip>
#include <map>
#include <mutex>
#include <openhab_msgs/msg/item_command.hpp>
#include <openhab_msgs/msg/item_state.hpp>
#include <openhab_msgs/srv/get_item.hpp>
#include <openhab_msgs/srv/list_items.hpp>
#include <openhab_msgs/srv/send_command.hpp>
#include <rclcpp/rclcpp.hpp>
#include <regex>
#include <set>
#include <sstream>
#include <std_msgs/msg/float64.hpp>
#include <std_msgs/msg/string.hpp>
#include <thread>

using openhab_msgs::msg::ItemCommand;
using openhab_msgs::msg::ItemState;
using openhab_msgs::srv::GetItem;
using openhab_msgs::srv::ListItems;
using openhab_msgs::srv::SendCommand;
using std_msgs::msg::Float64;
using namespace std::chrono_literals;

namespace {

std::string env(const char* name, const char* fallback) {
    const char* v = std::getenv(name);
    return v && *v ? v : fallback;
}

std::vector<std::string> clean(const std::vector<std::string>& v) {
    std::vector<std::string> out;
    for (const auto& s : v)
        if (!s.empty()) out.push_back(s);
    return out;
}

std::string baseType(std::string type, const std::string& groupType) {
    if (type == "Group" && !groupType.empty()) type = groupType;
    if (type.empty()) type = "String";
    return type.substr(0, type.find(':'));
}

std::vector<double> splitNumbers(const std::string& s, bool& ok) {
    std::vector<double> out;
    std::stringstream in(s);
    std::string part;
    ok = true;
    while (std::getline(in, part, ',')) {
        try {
            size_t used = 0;
            out.push_back(std::stod(part, &used));
            if (used != part.size()) ok = false;
        } catch (...) {
            ok = false;
        }
    }
    return out;
}

// Same rules as openhab_bridge/state.py
void parseState(ItemState& m, const std::string& groupType) {
    static const std::map<std::string, double> onOff = {
        {"ON", 1}, {"OFF", 0}, {"OPEN", 1}, {"CLOSED", 0}, {"PLAY", 1}, {"PAUSE", 0}};
    static const std::regex number(R"(^\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\s*(.*?)\s*$)");
    const std::string& s = m.state;
    if (s.empty() || s == "NULL" || s == "UNDEF") {
        m.is_null = true;
        return;
    }
    std::string kind = baseType(m.type, groupType);
    if (kind == "Switch" || kind == "Contact" || kind == "Player") {
        auto p = onOff.find(s);
        if (p != onOff.end()) m.has_number = true, m.number = p->second;
        return;
    }
    if (kind == "Color" || kind == "Location") {
        bool ok;
        auto values = splitNumbers(s, ok);
        if (!ok) return;
        m.values = values;
        if (kind == "Color" && values.size() == 3) m.has_number = true, m.number = values[2];
        return;
    }
    if (kind == "DateTime") {
        std::tm tm{};
        std::istringstream in(s.substr(0, 19));
        in >> std::get_time(&tm, "%Y-%m-%dT%H:%M:%S");
        if (in.fail()) return;
        long offset = 0;  // "+0100" or "+01:00" after the seconds/fraction
        std::smatch z;
        if (std::regex_search(s, z, std::regex(R"(([+-])(\d\d):?(\d\d)$)")))
            offset = (z[1] == "-" ? -1 : 1) * (std::stol(z[2]) * 3600 + std::stol(z[3]) * 60);
        m.has_number = true;
        m.number = static_cast<double>(timegm(&tm) - offset);
        return;
    }
    std::smatch r;
    if ((kind == "Number" || kind == "Dimmer" || kind == "Rollershutter" || kind == "String") &&
        std::regex_match(s, r, number)) {
        m.has_number = true;
        m.number = std::stod(r[1]);
        m.unit = r[2];
    }
}

}  // namespace

class OpenHABBridge : public rclcpp::Node {
public:
    OpenHABBridge()
        : Node("openhab_bridge"),
          url_(env("OPENHAB_URL", "http://127.0.0.1:8080")),
          token_(env("OPENHAB_TOKEN", "")),
          client_(url_, std::nullopt, std::nullopt, token_),
          items_(client_) {
        auto items = clean(declare_parameter<std::vector<std::string>>("items", {""}));
        auto groups = clean(declare_parameter<std::vector<std::string>>("groups", {""}));
        auto tags = clean(declare_parameter<std::vector<std::string>>("tags", {""}));
        std::string ns = declare_parameter<std::string>("namespace", "openhab");
        publishValue_ = declare_parameter<bool>("publish_value", true);
        source_ = declare_parameter<std::string>("command_source", "ros2");
        delay_ = declare_parameter<double>("reconnect_delay", 5.0);
        ns_ = "/" + ns.substr(ns.find_first_not_of('/'));

        for (const auto& name : resolve(items, groups, tags)) addItem(name);

        commandSub_ = create_subscription<ItemCommand>(
            ns_ + "/command", 10,
            [this](const ItemCommand& m) { send(m.name, m.command, m.update); });
        getSrv_ = create_service<openhab_msgs::srv::GetItem>(
            ns_ + "/get_item", [this](const std::shared_ptr<GetItem::Request> req,
                                  std::shared_ptr<GetItem::Response> res) { getItem(*req, *res); });
        sendSrv_ = create_service<openhab_msgs::srv::SendCommand>(
            ns_ + "/send_command", [this](const std::shared_ptr<SendCommand::Request> req,
                                      std::shared_ptr<SendCommand::Response> res) {
                std::tie(res->success, res->message) =
                    send(req->name, req->command, req->update);
            });
        listSrv_ = create_service<openhab_msgs::srv::ListItems>(
            ns_ + "/list_items", [this](const std::shared_ptr<ListItems::Request> req,
                                    std::shared_ptr<ListItems::Response> res) { listItems(*req, *res); });
        diagPub_ = create_publisher<diagnostic_msgs::msg::DiagnosticArray>("/diagnostics", 10);
        diagTimer_ = create_wall_timer(5s, [this] { publishDiagnostics(); });

        for (const char* k : {"events", "commands", "updates", "errors"}) counters_[k] = 0;
        reader_ = std::thread([this] { readEvents(); });
        RCLCPP_INFO(get_logger(), "bridge to %s: %zu items under %s/items", url_.c_str(),
                    statePub_.size(), ns_.c_str());
    }

    ~OpenHABBridge() override {
        stop_ = true;
        {
            std::lock_guard<std::mutex> lock(streamMutex_);
            if (stream_) stream_->interrupt();  // wakes up the reader thread
        }
        if (reader_.joinable()) reader_.join();
    }

private:
    std::vector<std::string> resolve(const std::vector<std::string>& items,
                                     const std::vector<std::string>& groups,
                                     const std::vector<std::string>& tags) {
        std::vector<std::string> wanted = items;
        for (const auto& g : groups) {
            openhab::json data = items_.getItem(g);
            if (openhab::isError(data)) {
                RCLCPP_ERROR(get_logger(), "group %s: %s", g.c_str(),
                             openhab::errorMessage(data).c_str());
                continue;
            }
            wanted.push_back(g);
            for (const auto& m : data.value("members", openhab::json::array()))
                wanted.push_back(m["name"]);
        }
        for (const auto& t : tags) {
            openhab::json data = items_.getItems(std::nullopt, t, ".*", false, "name");
            if (!openhab::isError(data))
                for (const auto& i : data) wanted.push_back(i["name"]);
        }
        if (items.empty() && groups.empty() && tags.empty()) {
            openhab::json data = items_.getItems(std::nullopt, std::nullopt, ".*", false, "name");
            if (!openhab::isError(data))
                for (const auto& i : data) wanted.push_back(i["name"]);
        }
        std::vector<std::string> unique;
        std::set<std::string> seen;
        for (const auto& n : wanted)
            if (seen.insert(n).second) unique.push_back(n);
        return unique;
    }

    void addItem(const std::string& name) {
        openhab::json data = items_.getItem(name, "");
        if (openhab::isError(data)) {
            RCLCPP_ERROR(get_logger(), "item %s: %s", name.c_str(),
                         openhab::errorMessage(data).c_str());
            return;
        }
        types_[name] = {data.value("type", "String"), data.value("groupType", "")};
        auto qos = rclcpp::QoS(1).reliable().transient_local();
        std::string base = ns_ + "/items/" + name;
        statePub_[name] = create_publisher<ItemState>(base + "/state", qos);
        if (publishValue_) valuePub_[name] = create_publisher<Float64>(base + "/value", qos);
        commandSubs_.push_back(create_subscription<std_msgs::msg::String>(
            base + "/command", 10,
            [this, name](const std_msgs::msg::String& m) { send(name, m.data, false); }));
        publish(name, data.value("state", ""));
    }

    ItemState makeState(const std::string& name, const std::string& state) {
        ItemState m;
        m.header.stamp = now();
        m.header.frame_id = "openhab";
        m.name = name;
        auto t = types_.find(name);
        m.type = t != types_.end() ? t->second.first : "String";
        m.state = state;
        parseState(m, t != types_.end() ? t->second.second : "");
        return m;
    }

    void publish(const std::string& name, const std::string& state) {
        auto p = statePub_.find(name);
        if (p == statePub_.end()) return;
        ItemState m = makeState(name, state);
        p->second->publish(m);  // publish() is thread-safe
        auto v = valuePub_.find(name);
        if (m.has_number && v != valuePub_.end()) {
            Float64 f;
            f.data = m.number;
            v->second->publish(f);
        }
    }

    void readEvents() {
        openhab::OpenHABClient client(url_, std::nullopt, std::nullopt, token_);  // own client
        openhab::Items items(client);
        openhab::ItemEvents events(client);
        while (!stop_ && rclcpp::ok()) {
            {
                std::lock_guard<std::mutex> lock(streamMutex_);
                stream_ = std::make_unique<openhab::EventStream>(events.ItemStateChangedEvent());
            }
            if (stream_->isError()) {
                setConnected(false, stream_->error());
                wait();
                continue;
            }
            setConnected(true);
            for (const auto& [name, pub] : statePub_) {  // nothing lost during a disconnect
                openhab::json s = items.getItemState(name);
                if (s.is_string()) publish(name, s.get<std::string>());
            }
            for (const openhab::json& e : *stream_) {
                std::string topic = e.value("topic", "");
                std::string name = topic.substr(14, topic.find('/', 14) - 14);
                if (statePub_.count(name) && e["payload"].contains("value")) {
                    ++counters_["events"];
                    publish(name, e["payload"]["value"].get<std::string>());
                }
            }
            if (stop_) return;
            setConnected(false, "event stream ended");
            wait();
        }
    }

    void wait() {
        auto until = std::chrono::steady_clock::now() + std::chrono::duration<double>(delay_);
        while (!stop_ && std::chrono::steady_clock::now() < until) std::this_thread::sleep_for(100ms);
    }

    void setConnected(bool ok, const std::string& reason = "") {
        if (ok != connected_) {
            if (ok)
                RCLCPP_INFO(get_logger(), "connected to openHAB");
            else
                RCLCPP_WARN(get_logger(), "openHAB not reachable: %s", reason.c_str());
        }
        connected_ = ok;
    }

    std::pair<bool, std::string> send(const std::string& name, const std::string& command,
                                      bool update) {
        openhab::json r = update ? items_.postUpdate(name, command, source_)
                                 : items_.sendCommand(name, command, source_);
        if (openhab::isError(r)) {
            ++counters_["errors"];
            RCLCPP_ERROR(get_logger(), "%s <- %s: %s", name.c_str(), command.c_str(),
                         openhab::errorMessage(r).c_str());
            return {false, openhab::errorMessage(r)};
        }
        ++counters_[update ? "updates" : "commands"];
        RCLCPP_INFO(get_logger(), "%s <- %s%s", name.c_str(), command.c_str(),
                    update ? " (update)" : "");
        return {true, "OK"};
    }

    void getItem(const openhab_msgs::srv::GetItem::Request& req,
                 openhab_msgs::srv::GetItem::Response& res) {
        openhab::json data = items_.getItem(req.name, "");
        if (openhab::isError(data)) {
            res.success = false;
            res.message = openhab::errorMessage(data);
            return;
        }
        types_.emplace(req.name,
                       std::make_pair(data.value("type", "String"), data.value("groupType", "")));
        res.item = makeState(req.name, data.value("state", ""));
        res.success = true;
        res.message = "OK";
    }

    void listItems(const openhab_msgs::srv::ListItems::Request& req,
                   openhab_msgs::srv::ListItems::Response& res) {
        auto opt = [](const std::string& s) {
            return s.empty() ? std::nullopt : std::optional<std::string>(s);
        };
        openhab::json data =
            items_.getItems(opt(req.type), opt(req.tags), ".*", false, "name,type,label");
        if (openhab::isError(data)) {
            res.success = false;
            res.message = openhab::errorMessage(data);
            return;
        }
        std::map<std::string, openhab::json> sorted;
        for (const auto& i : data) sorted[i["name"]] = i;
        for (const auto& [name, i] : sorted) {
            res.names.push_back(name);
            res.types.push_back(i.value("type", ""));
            res.labels.push_back(i.contains("label") && i["label"].is_string() ? i["label"] : "");
            res.bridged.push_back(statePub_.count(name) > 0);
        }
        res.success = true;
        res.message = std::to_string(data.size()) + " items";
    }

    void publishDiagnostics() {
        diagnostic_msgs::msg::DiagnosticStatus s;
        s.name = "openhab_bridge";
        s.hardware_id = url_;
        s.level = connected_ ? s.OK : s.ERROR;
        s.message = connected_ ? "connected" : "openHAB not reachable";
        auto kv = [](const std::string& k, const std::string& v) {
            diagnostic_msgs::msg::KeyValue p;
            p.key = k;
            p.value = v;
            return p;
        };
        s.values.push_back(kv("items", std::to_string(statePub_.size())));
        for (const char* k : {"events", "commands", "updates", "errors"})
            s.values.push_back(kv(k, std::to_string(counters_[k].load())));
        diagnostic_msgs::msg::DiagnosticArray a;
        a.header.stamp = now();
        a.status.push_back(s);
        diagPub_->publish(a);
    }

    std::string url_, token_, ns_, source_;
    double delay_ = 5.0;
    bool publishValue_ = true;
    openhab::OpenHABClient client_;
    openhab::Items items_;
    std::map<std::string, std::pair<std::string, std::string>> types_;
    std::map<std::string, rclcpp::Publisher<ItemState>::SharedPtr> statePub_;
    std::map<std::string, rclcpp::Publisher<Float64>::SharedPtr> valuePub_;
    std::vector<rclcpp::Subscription<std_msgs::msg::String>::SharedPtr> commandSubs_;
    rclcpp::Subscription<ItemCommand>::SharedPtr commandSub_;
    rclcpp::Service<openhab_msgs::srv::GetItem>::SharedPtr getSrv_;
    rclcpp::Service<openhab_msgs::srv::SendCommand>::SharedPtr sendSrv_;
    rclcpp::Service<openhab_msgs::srv::ListItems>::SharedPtr listSrv_;
    rclcpp::Publisher<diagnostic_msgs::msg::DiagnosticArray>::SharedPtr diagPub_;
    rclcpp::TimerBase::SharedPtr diagTimer_;
    std::map<std::string, std::atomic<long>> counters_;
    std::atomic<bool> stop_{false}, connected_{false};
    std::mutex streamMutex_;
    std::unique_ptr<openhab::EventStream> stream_;
    std::thread reader_;
};

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    try {
        rclcpp::spin(std::make_shared<OpenHABBridge>());
    } catch (const std::exception& e) {
        std::cerr << "openhab_bridge: " << e.what() << "\n";
        rclcpp::shutdown();
        return 1;
    }
    rclcpp::shutdown();
    return 0;
}
