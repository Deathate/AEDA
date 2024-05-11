#include <bits/stdc++.h>

using namespace std;

class FFproperty {
   public:
    string FFname;
    int bits, power, area;

    FFproperty() {
        this->FFname = "";
        this->bits = 0, this->power = 0, this->area = 0;
    }
};

class FF {
   public:
    string FFIP, FFname;
    int x, y;

    FF() {
        this->FFIP = "", this->FFname = "";
        this->x = 0, this->y = 0;
    }
};

class Pin {
   public:
    bool is_input;
    string pinname;
    int x, y;

    Pin() {
        this->is_input = false;
        this->pinname = "";
        this->x = 0, this->y = 0;
    }
};

class NetList {
   public:
    string pinname, FFname;
    int slack;

    NetList() {
        this->pinname = "", this->FFname = "";
        this->slack = 0;
    }
};

class INOUTcounter {
   public:
    int input, output;

    INOUTcounter() {
        this->input = 0, this->output = 0;
    }
};

int main(int argc, char *argv[]) {
    if (argc < 3) {
        cout << "USAGE ./SolutionChecker [input file] [output file]\n";
        return -1;
    }

    ifstream in_file(argv[1]);
    if (!in_file.is_open()) {
        cout << "INPUT FILE OPEN FAILED.\n";
        return -1;
    }

    string line = "", tok = "", ff_name = "";
    stringstream ss;

    int chip_sizex = 0, chip_sizey = 0;
    int grid_sizex = 0, grid_sizey = 0;
    int bin_sizex = 0, bin_sizey = 0;
    int slack = 0;

    unordered_map<string, FFproperty *> FF_map;
    unordered_map<string, FF *> FF_list;
    unordered_map<string, Pin *> pin_list;
    unordered_map<string, NetList *> net_list;

    unordered_map<string, set<string> > ff_pins;

    getline(in_file, line);
    ss.clear(), ss.str(line);
    ss >> tok >> chip_sizex >> tok >> chip_sizey;
    getline(in_file, line);
    ss.clear(), ss.str(line);
    ss >> tok >> grid_sizex >> tok >> grid_sizey;
    getline(in_file, line);
    ss.clear(), ss.str(line);
    ss >> tok >> bin_sizex >> tok >> bin_sizey;
    getline(in_file, line);

    bool in_FF_list = false, in_pin_list = false, in_net_list = false;

    while (getline(in_file, line)) {
        if (line.find("FLIP_FLOP ") != string::npos) {
            line = line.substr(1, line.length() - 2);
            // cout << line << '\n';
            ff_name = line.substr(line.find(" ") + 1, string::npos);

            FF_map[ff_name] = new FFproperty();
            FF_map[ff_name]->FFname = ff_name;

            getline(in_file, line);
            ss.clear(), ss.str(line);
            ss >> tok >> FF_map[ff_name]->bits;
            getline(in_file, line);
            ss.clear(), ss.str(line);
            ss >> tok >> FF_map[ff_name]->power;
            getline(in_file, line);
            ss.clear(), ss.str(line);
            ss >> tok >> FF_map[ff_name]->area;
        }

        if (line.find("[FLIP_FLOP_LIST]") != string::npos)
            in_FF_list = true;
        else if (line.find("[END FLIP_FLOP_LIST]") != string::npos)
            in_FF_list = false;
        else if (in_FF_list) {
            ss.clear(), ss.str(line);
            ss >> tok >> ff_name;
            FF_list[ff_name] = new FF();
            FF_list[ff_name]->FFIP = tok;
            FF_list[ff_name]->FFname = ff_name;

            ss >> tok;
            tok = tok.substr(1, tok.length() - 2);
            FF_list[ff_name]->x = stoi(tok.substr(0, tok.find(",")));
            FF_list[ff_name]->y = stoi(tok.substr(tok.find(",") + 1, string::npos));
        }

        if (line.find("[PIN_LIST]") != string::npos)
            in_pin_list = true;
        else if (line.find("[END PIN_LIST]") != string::npos)
            in_pin_list = false;
        else if (in_pin_list) {
            ss.clear(), ss.str(line);
            ss >> tok >> ff_name;
            pin_list[ff_name] = new Pin();
            if (tok == "INPUT") pin_list[ff_name]->is_input = true;
            pin_list[ff_name]->pinname = ff_name;

            ss >> tok;
            tok = tok.substr(1, tok.length() - 2);
            pin_list[ff_name]->x = stoi(tok.substr(0, tok.find(",")));
            pin_list[ff_name]->y = stoi(tok.substr(tok.find(",") + 1, string::npos));
        }

        if (line.find("[NET_LIST]") != string::npos)
            in_net_list = true;
        else if (line.find("[END NET_LIST]") != string::npos)
            in_net_list = false;
        else if (in_net_list) {
            ss.clear(), ss.str(line);
            ss >> tok >> ff_name >> slack;

            net_list[tok] = new NetList();
            net_list[tok]->pinname = tok;
            net_list[tok]->FFname = ff_name;
            net_list[tok]->slack = slack;
            ff_pins[ff_name].insert(tok);
        }
    }

    int dist = 0;
    unordered_map<string, int> total_slacks;

    for (auto &net : net_list) {
        dist = abs(pin_list.at(net.second->pinname)->x - FF_list.at(net.second->FFname)->x) + abs(pin_list.at(net.second->pinname)->y - FF_list.at(net.second->FFname)->y) + net.second->slack;
        total_slacks[net.second->pinname] = dist;
        // std::cout << net.second->pinname << '\n';
        // std::cout << dist << '\n';
    }

    for (auto &i : FF_map) {
        // cout << i.first << '\n';
    }

    ifstream out_file(argv[2]);

    if (!out_file.is_open()) {
        cout << "OUTPUT FILE OPEN FAILED.\n";
        return -1;
    }

    unordered_map<string, pair<FF *, INOUTcounter> > out_FF_list;
    unordered_map<string, NetList *> out_net_list;
    unordered_map<string, set<string> > out_ff_pins;
    unordered_map<string, int> out_pin_sets;

    in_FF_list = false, in_net_list = false;

    size_t line_cnt = 0;

    while (getline(out_file, line)) {
        line_cnt++;
        // cout << line << '\n';
        if (line.find("[FLIP_FLOP_LIST]") != string::npos)
            in_FF_list = true;
        else if (line.find("[END FLIP_FLOP_LIST]") != string::npos)
            in_FF_list = false;
        else if (in_FF_list) {
            ss.clear(), ss.str(line);
            ss >> tok >> ff_name;
            // cout << tok << " " << ff_name << '\n';
            out_FF_list[ff_name] = make_pair(new FF(), INOUTcounter());
            out_FF_list[ff_name].first->FFIP = tok;
            out_FF_list[ff_name].first->FFname = ff_name;

            if (FF_map.find(out_FF_list[ff_name].first->FFIP) == FF_map.end()) {
                cout << "ON LINE " << line_cnt << '\n';
                cout << "UNDEFINED FLIP FLOP PROPERTY [" << out_FF_list[ff_name].first->FFIP << "] at FF [" << out_FF_list[ff_name].first->FFname << "]. O.O\n";
                return -1;
            }

            ss >> tok;
            tok = tok.substr(1, tok.length() - 2);
            // cout << tok << '\n';
            out_FF_list[ff_name].first->x = stoi(tok.substr(0, tok.find(",")));
            out_FF_list[ff_name].first->y = stoi(tok.substr(tok.find(",") + 1, string::npos));

            // cout << out_FF_list[ff_name].first->x << ", " << out_FF_list[ff_name].first->y << '\n';

            if (out_FF_list[ff_name].first->x % grid_sizex != 0 || out_FF_list[ff_name].first->y % grid_sizey != 0) {
                cout << "ON LINE " << line_cnt << '\n';
                cout << "OOPS! FLIP FLOP PLACEMENT NOT ON GRID. X.X"
                     << "\nFF_NAME : " << out_FF_list[ff_name].first->FFname << '\n';
            }

            if (out_FF_list[ff_name].first->x < 0 || out_FF_list[ff_name].first->x > chip_sizex) {
                cout << "ON LINE " << line_cnt << '\n';
                cout << "OOPS! FLIP FLOP X-axis PLACEMENT OUT OF RANGE ( 0 ~ " << chip_sizex << " ). X.X"
                     << "\nFF_NAME : " << out_FF_list[ff_name].first->FFname
                     << "\nFF_PROPERTY : " << out_FF_list[ff_name].first->FFIP
                     << "\nFF X_coordinate : " << out_FF_list[ff_name].first->x << '\n';
                return -1;
            }
            if (out_FF_list[ff_name].first->y < 0 || out_FF_list[ff_name].first->y > chip_sizey) {
                cout << "ON LINE " << line_cnt << '\n';
                cout << "OOPS! FLIP FLOP Y-axis PLACEMENT OUT OF RANGE ( 0 ~ " << chip_sizey << " ). X.X"
                     << "\nFF_NAME : " << out_FF_list[ff_name].first->FFname
                     << "\nFF_PROPERTY : " << out_FF_list[ff_name].first->FFIP
                     << "\nFF Y_coordinate : " << out_FF_list[ff_name].first->y << '\n';
                return -1;
            }
        }

        if (line.find("[NET_LIST]") != string::npos)
            in_net_list = true;
        else if (line.find("[END NET_LIST]") != string::npos)
            in_net_list = false;
        else if (in_net_list) {
            ss.clear(), ss.str(line);
            ss >> tok >> ff_name >> slack;

            out_net_list[tok] = new NetList();
            out_net_list[tok]->pinname = tok;
            out_net_list[tok]->FFname = ff_name;
            out_net_list[tok]->slack = slack;

            if (pin_list.find(out_net_list[tok]->pinname) == pin_list.end()) {
                cout << "ON LINE " << line_cnt << '\n';
                cout << "UNDEFINED PIN NAME [" << out_net_list[tok]->pinname << "]. O.O\n";
                return -1;
            }
            if (out_FF_list.find(out_net_list[tok]->FFname) == out_FF_list.end()) {
                cout << "ON LINE " << line_cnt << '\n';
                cout << "UNDEFINED FLIP FLOP NAME [" << out_net_list[tok]->FFname << "]. O.O\n";
                return -1;
            }

            if (pin_list.at(out_net_list[tok]->pinname)->is_input) {
                out_FF_list.at(out_net_list[tok]->FFname).second.input++;
                if (out_FF_list.at(out_net_list[tok]->FFname).second.input > FF_map[out_FF_list[out_net_list[tok]->FFname].first->FFIP]->bits) {
                    cout << "ON LINE " << line_cnt << '\n';
                    cout << "FF " << ff_name << " INPUT PIN NUMBER OVERFLOW. O.O\n";
                    return -1;
                }
            } else {
                out_FF_list.at(out_net_list[tok]->FFname).second.output++;
                if (out_FF_list.at(out_net_list[tok]->FFname).second.output > FF_map[out_FF_list[out_net_list[tok]->FFname].first->FFIP]->bits) {
                    cout << "ON LINE " << line_cnt << '\n';
                    cout << "FF " << ff_name << " OUTPUT PIN NUMBER OVERFLOW. O.O\n";
                    return -1;
                }
            }

            out_ff_pins[ff_name].insert(tok);

            int x_diff = abs(pin_list.at(tok)->x - out_FF_list.at(ff_name).first->x);
            int y_diff = abs(pin_list.at(tok)->y - out_FF_list.at(ff_name).first->y);

            dist = total_slacks[tok] - x_diff - y_diff;

            if (dist != slack) {
                cout << "ON LINE " << line_cnt << '\n';
                cout << "OOPS! WRONG SLACK. X.X"
                     << "\nPIN : " << tok
                     << "\nFLIP FLOP : " << ff_name
                     << "\nGOLDEN SLACK : " << dist
                     << "\nYOUR SLACK : " << slack;
                return -1;
            }
            if (slack < 0) {
                cout << "ON LINE " << line_cnt << '\n';
                cout << "OOPS! SLACK < 0. X.X\n";
                return -1;
            }
        }
    }

    int set_num = 0;
    for (auto &i : out_ff_pins) {
        for (auto &j : i.second) {
            out_pin_sets[j] = set_num;
        }
        set_num++;
    }

    int now_set = -1;
    for (auto &i : ff_pins) {
        for (auto &j : i.second) {
            if (now_set == -1)
                now_set = out_pin_sets[j];
            else {
                if (now_set != out_pin_sets[j]) {
                    cout << "OOPS! WRONG PIN CONNECTION. X.X";
                    cout << "\n [OUTPUT PIN, FF SET]: ";
                    for (auto &k : i.second) cout << "[" << k << ", " << out_pin_sets[k] << "], ";
                    cout << '\n';
                    return -1;
                }
            }
        }
        now_set = -1;
    }

    int total_p = 0;

    for (auto ff : out_FF_list) {
        total_p += FF_map[ff.second.first->FFIP]->power;
    }

    cout << "CONGRATE! YOUR CHIP SEEMS WORK with total power : " << total_p << '\n';

    return 0;
}