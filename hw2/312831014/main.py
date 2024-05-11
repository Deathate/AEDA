# %%
# ./Lab2 [input file name] [output file name]
import sys
from collections import defaultdict
from dataclasses import dataclass

import networkx as nx
import numpy as np
import shapely
from llist import dllist, sllist
from shapely.geometry import LineString, Point, Polygon

from utility import HiddenPrints, exit

TEST = False
if TEST:
    from plot import PlotlyUtility
else:
    from plot_dummy import PlotlyUtility


if len(sys.argv) != 3:
    filein = "cases/c5.in"
    fileout = "c2.out"
else:
    _, filein, fileout = sys.argv

flip_flop_flag = False
flip_flop_list = {}
pin_flag = False
net_flag = False
library_flag = False
library_list = {}
library_sorted = []
library_dict = {}


def cityblock(arr1, arr2):
    return np.sum(np.abs(np.array(arr1) - np.array(arr2)))


def rotate_45(intersection_coord):
    intersection_coord[:, 0], intersection_coord[:, 1] = intersection_coord[:, 0] + \
        intersection_coord[:, 1], intersection_coord[:, 1] - intersection_coord[:, 0]


@dataclass(slots=True, frozen=True)
class FlipFlop:
    library: str
    name: str
    pos: tuple

    def bit_number(self, library_list):
        return library_list[self.library].bit_number


@dataclass(slots=True, frozen=True)
class Pin:
    name: str
    pos: tuple


@dataclass(slots=True)
class Lib:
    name: str = ""
    bit_number: int = 0
    power: int = 0
    area: int = 0


def slack_region(pos, slack):
    x, y = pos
    return Polygon([(x, y + slack), (x + slack, y), (x, y - slack), (x - slack, y)])


grid_x = 0
grid_y = 0

G = nx.Graph()
for i, line in enumerate(open(filein).readlines()):
    line = line.strip()
    part = line.split()
    # read grid size
    if part[0] == "GRID_SIZE":
        grid_x, grid_y = int(part[1]), int(part[3])

    # read library
    if line == "[FLIP_FLOP_PROPERTY]":
        library_flag = True
    elif line == "[END LIBRARY]":
        library_flag = False
    elif library_flag:
        if part[0] == "[FLIP_FLOP":
            lib_name = part[1][:-1]
            library_list[lib_name] = Lib(name=lib_name)
        else:
            if part[0] == "BIT_NUMBER":
                library_list[lib_name].bit_number = int(part[1])
            elif part[0] == "POWER_CONSUMPTION":
                library_list[lib_name].power = int(part[1])
            elif part[0] == "AREA":
                library_list[lib_name].area = int(part[1])

    # read flip flop list
    if line == "[FLIP_FLOP_LIST]":
        flip_flop_flag = True
    elif line == "[END FLIP_FLOP_LIST]":
        flip_flop_flag = False
    elif flip_flop_flag:
        lib = part[0]
        name = part[1]
        x, y = part[2].split(",")
        x = int(x[1:])
        y = int(y[:-1])
        flip_flop_list[name] = FlipFlop(lib, name, (x, y))
        G.add_node(name, library=lib, meta=flip_flop_list[name])

    # read pin list
    if line == "[PIN_LIST]":
        pin_flag = True
    elif line == "[END PIN_LIST]":
        pin_flag = False
    elif pin_flag:
        name = part[1]
        x, y = part[2].split(",")
        x = int(x[1:])
        y = int(y[:-1])
        G.add_node(name, meta=Pin(name, (x, y)))

    # read netlist
    if line == "[NET_LIST]":
        net_flag = True
    elif line == "[END NET_LIST]":
        net_flag = False
    elif net_flag:
        pin_name = part[0]
        ff = part[1]
        slack = int(part[2])
        ff_n = G.nodes[ff]
        tsfr = cityblock(G.nodes[ff]["meta"].pos, G.nodes[pin_name]["meta"].pos) + slack
        G.add_edge(ff, pin_name, tsfr=tsfr)


for name, k in library_list.items():
    library_sorted.append(k)
    library_dict[k.bit_number] = k
library_sorted.reverse()
flip_flop_names = list(flip_flop_list.keys())

P1 = PlotlyUtility()
interval_graph_x = []
interval_graph_y = []
for ffidx, ff in enumerate(flip_flop_names):
    node = G.nodes[ff]
    tsfr = [slack_region(G.nodes[v]["meta"].pos, data) for u, v, data in G.edges(ff, data="tsfr")]
    intersection = shapely.intersection_all(tsfr)
    intersection_coord = shapely.get_coordinates(intersection)

    rotate_45(intersection_coord)
    node["region"] = intersection
    P1.add_rectangle(intersection_coord)
    regionx, regiony = intersection_coord[:, 0], intersection_coord[:, 1]
    xstart, xend = regionx.min(), regionx.max()
    ystart, yend = regiony.min(), regiony.max()
    if xstart >= xend:
        xend += (xstart - xend) + 1e-8
    if ystart >= yend:
        yend += (ystart - yend) + 1e-8
    interval_graph_x.append((xstart, ffidx, True))
    interval_graph_x.append((xend, ffidx, False))
    interval_graph_y.append((ystart, ffidx, True))
    interval_graph_y.append((yend, ffidx, False))


interval_graph_x.sort(key=lambda x: (x[0], x[2]))
interval_graph_x = sllist(interval_graph_x)
interval_graph_y.sort(key=lambda x: (x[0], x[2]))
interval_graph_y = sllist(interval_graph_y)

interval_graph_x_inv = defaultdict(list)
interval_graph_y_inv = defaultdict(list)
current_node = interval_graph_x.first
i = 0
while current_node:
    interval_graph_x_inv[current_node.value[1]].append(current_node)
    current_node = current_node.next
    i += 1
current_node = interval_graph_y.first
while current_node:
    interval_graph_y_inv[current_node.value[1]].append(current_node)
    current_node = current_node.next
# P1.show()

K = []
kall = set(range(len(flip_flop_names)))


def cluster(required_endpoint):
    print("!!!!!!!!!!!!!!!!")
    related_ff = set()
    related_ff_ls = dllist()
    related_ff_ls_inv = defaultdict(list)
    current_node = interval_graph_x.first
    any_decision = False
    while current_node:
        ff_name, ff_is_start = current_node.value[1], current_node.value[2]
        related_ff_ls.append(current_node)
        related_ff_ls_inv[current_node.value[1]].append(related_ff_ls.last)

        print("--", ff_name, related_ff_ls.size)
        print(current_node, current_node.next)
        # found decision point
        if related_ff_ls.size > 1 and not related_ff_ls.last.value.value[2] and related_ff_ls.last.prev.value.value[2] and related_ff_ls.last.value.value[1] != related_ff_ls.last.prev.value.value[1]:
            y_interval_start = False
            related_ff_y = set()
            related_ff_y_ls = dllist()
            max_clique = []
            current_node_y = interval_graph_y.first
            print(f"decision point x {ff_name}, len {len(interval_graph_x)}")
            while current_node_y:
                ff_name_y, ff_is_start_y = current_node_y.value[1], current_node_y.value[2]
                if ff_name_y in related_ff:
                    related_ff_y_ls.append(current_node_y)
                    if y_interval_start and ff_name_y == ff_name and not ff_is_start_y and required_endpoint:
                        break
                    if y_interval_start and not related_ff_y_ls.last.value.value[2] and related_ff_y_ls.last.prev.value.value[2]:
                        print(f"decision point y {ff_name_y}")
                        if len(new_clique := related_ff_y.intersection(related_ff)) > len(max_clique):
                            max_clique = new_clique
                            print("update", max_clique)
                            if len(max_clique) >= library_sorted[0].bit_number:
                                break
                    if y_interval_start and ff_name_y == ff_name and not ff_is_start_y and not required_endpoint:
                        break
                    if ff_name_y == ff_name and ff_is_start_y:
                        y_interval_start = True

                    if ff_is_start_y:
                        related_ff_y.add(ff_name_y)
                        print("+", ff_name_y)
                    else:
                        related_ff_y.remove(ff_name_y)
                        print("-", ff_name_y)
                current_node_y = current_node_y.next
            if len(max_clique) > 0:
                # find appropriate library
                B = 0
                clique_size = sum([flip_flop_list[flip_flop_names[c]].bit_number(library_list)
                                   for c in max_clique])
                max_clique.remove(ff_name)
                for lib in library_sorted:
                    if lib.bit_number <= clique_size:
                        B = lib.bit_number
                        print(f"choose lib {lib.bit_number}")
                        break
                Btmp = B
                decision_point_ff = flip_flop_list[flip_flop_names[ff_name]]
                B -= decision_point_ff.bit_number(library_list)
                print("remain size", B)
                k = [ff_name]

                max_clique = list(max_clique)
                max_clique.sort(key=lambda x: flip_flop_list[flip_flop_names[x]].bit_number(
                    library_list), reverse=True)
                for c in max_clique:
                    bit = flip_flop_list[flip_flop_names[c]].bit_number(library_list)
                    t = B - bit
                    if t >= 0:
                        print("select", c, bit)
                        B = t
                        k.append(c)
                    if t == 0:
                        break

                if B != 0:
                    print("error")
                    for c in max_clique:
                        bit = flip_flop_list[flip_flop_names[c]].library
                        print(c, bit)
                    current_node = current_node.next
                else:
                    any_decision = True
                    print("max_clique", k)
                    K.append({"bit": Btmp, "ff": k})
                    print("remove", k)
                    tmp = current_node.next
                    while tmp.value[1] in k:
                        tmp = tmp.next
                    current_node = tmp
                    print("current_node move to", current_node)
                    for kele in k:
                        for node in interval_graph_x_inv[kele]:
                            interval_graph_x.remove(node)
                        for node in related_ff_ls_inv[kele]:
                            related_ff_ls.remove(node)
                        for node in interval_graph_y_inv[kele]:
                            interval_graph_y.remove(node)
                        if kele != ff_name:
                            related_ff.remove(kele)
                    kall.difference_update(k)

            else:
                print("no clique found")
                current_node = current_node.next

        else:
            current_node = current_node.next
        print("related ff")
        print(related_ff)
        if ff_is_start:
            related_ff.add(ff_name)
            print("+", ff_name)
        else:
            related_ff.remove(ff_name)
            print("-", ff_name)
    return any_decision


with HiddenPrints():
    cluster(required_endpoint=False)
    cluster(required_endpoint=False)


for k in kall:
    ff = flip_flop_list[flip_flop_names[k]]
    K.append({"bit": library_list[ff.library].bit_number, "ff": [k]})

with open(fileout, "w") as f:
    total_power = 0
    P2 = PlotlyUtility(update_layout=True)
    net_list = []
    print("[FLIP_FLOP_LIST]", file=f)
    for k in K:
        tsfr = [G.nodes[flip_flop_names[kele]]["region"] for kele in k["ff"]]
        ff_name_new = str(k["ff"]).replace(" ", "")
        ff_name_new = f"ff_{ff_name_new}"
        ff_name_new = "ff_" + ",".join([flip_flop_names[kele] for kele in k["ff"]])
        intersection = shapely.intersection_all(tsfr)
        intersection_coord = shapely.get_coordinates(intersection)
        if not intersection.is_empty:
            # find the position of the new flip-flop
            ff_pos_new = np.array(shapely.centroid(intersection).coords, dtype=int)[0]
            ff_pos_new[0], ff_pos_new[1] = ff_pos_new[0] // grid_x * \
                grid_x, ff_pos_new[1] // grid_y * grid_y
            ff_pos_new = tuple(ff_pos_new)
            if Point(ff_pos_new).intersection(intersection).is_empty:
                if isinstance(intersection, Polygon):
                    ff_pos_new = np.array(intersection.exterior.coords, dtype=int)
                else:
                    ff_pos_new = np.array(intersection.coords, dtype=int)
                grid_box = []
                minx = ff_pos_new[:, 0].min() // grid_x * grid_x
                maxx = ff_pos_new[:, 0].max() // grid_x * grid_x
                miny = ff_pos_new[:, 1].min() // grid_y * grid_y
                maxy = ff_pos_new[:, 1].max() // grid_y * grid_y
                selection = None
                for i in range(minx, maxx, grid_x):
                    its = LineString([(i, miny), (i, maxy)]).intersection(intersection)
                    if not its.is_empty:
                        selection = its
                        break
                else:
                    for i in range(miny, maxy, grid_y):
                        its = LineString([(minx, i), (maxx, i)]).intersection(intersection)
                        if not its.is_empty:
                            selection = its
                            break
                assert selection is not None
                ff_pos_new = np.array(its.coords, dtype=int)[0]
                ff_pos_new = tuple(ff_pos_new)
            # draw the new flip-flop
            rotate_45(intersection_coord)
            color_id = 0 if len(k["ff"]) == 1 else 1
            P2.change_group(color_id)
            P2.add_rectangle(intersection_coord, color_id=color_id, label=k["ff"])

            ff_pos_new_str = str(ff_pos_new).replace(" ", "")
            print(f"{library_dict[k['bit']].name} {ff_name_new} {ff_pos_new_str}", file=f)
            total_power += library_dict[k['bit']].power
            for kele in k["ff"]:
                connected_pin = G[flip_flop_names[kele]]
                for name in connected_pin:
                    pin_pos = G.nodes[name]["meta"].pos
                    total_slack = list(G.edges(name, data="tsfr"))[0][2]
                    remain_slack = total_slack - cityblock(pin_pos, ff_pos_new)
                    # if remain_slack < 0:
                    #     # print(G.nodes[name])
                    #     # print(ff_pos_new)
                    #     # print(shapely.centroid(intersection))
                    #     # exit()
                    #     from plot import PlotlyUtility
                    #     Ptest = PlotlyUtility()
                    #     for ts, kele in zip(tsfr, k["ff"]):
                    #         Ptest.add_rectangle(slack_region(
                    #             G.nodes[flip_flop_names[kele]]["meta"].pos, 5), name)
                    #         Ptest.change_group(0)
                    #         Ptest.add_rectangle(ts, kele, color_id=0)
                    #     Ptest.change_color()
                    #     Ptest.add_rectangle(intersection, " ")
                    #     print(intersection.area)
                    #     Ptest.show()
                    net_list.append((name, ff_name_new, remain_slack))
        else:
            print(len(tsfr))
            print(k)
            Ptest = PlotlyUtility()
            for ts, kele in zip(tsfr, k["ff"]):
                Ptest.add_rectangle(shapely.get_coordinates(ts), kele)
            Ptest.show()
            exit()

    print("[END FLIP_FLOP_LIST]", file=f)

    print("[NET_LIST]", file=f)
    for net in net_list:
        print(f"{net[0]} {net[1]} {net[2]}", file=f)
    print("[END NET_LIST]", file=f)
    if TEST:
        print("total power", total_power)

# P2.change_color()
# for k in kall:
#     intersection = G.nodes[flip_flop_names[k]]["region"]
#     intersection_coord = shapely.get_coordinates(intersection)
#     tmp = intersection_coord.copy()
#     intersection_coord[:, 0] = tmp[:, 0] + tmp[:, 1]
#     intersection_coord[:, 1] = tmp[:, 1] - tmp[:, 0]
#     text = str(k) + "," + str(flip_flop_list[flip_flop_names[k]].bit_number(library_list))
#     P2.add_rectangle(intersection_coord)
    # P2.add_rectangle(intersection_coord, text)
P1.show(save=True)
P2.show()
