# ./Lab1 [input file name] [output file name]
import sys
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
from shapely import Point, Polygon, STRtree


def get_square_param(lb, ub):
    return [lb, [lb[0], ub[1]], ub, [ub[0], lb[1]]]


_, filein, fileout = sys.argv

routed_shape = []
routed_shape_layer = {}
routed_via = []
routed_via_layer = {}


@dataclass(frozen=True)
class Cell():
    __slots__ = ['layer', 'lb', 'ub', 'via']
    layer: str
    lb: tuple
    ub: tuple
    via: bool


for line in open(filein).readlines():
    line = line.strip()
    lsplit = line.split(' ')
    if lsplit[0] == "RoutedShape":
        layer, lp, up = lsplit[1:]
        if layer not in routed_shape_layer:
            routed_shape_layer[layer] = len(routed_shape_layer)
            routed_shape.append([])
        routed_shape[routed_shape_layer[layer]].append(
            Cell(layer, eval(lp), eval(up), False))
    elif lsplit[0] == "RoutedVia":
        layer, lp = lsplit[1:]
        if layer not in routed_via_layer:
            routed_via_layer[layer] = len(routed_via_layer)
            routed_via.append([])
        routed_via[routed_via_layer[layer]].append(
            Cell(layer, eval(lp), None, True))

shape_polygon = [[Polygon(get_square_param(x.lb, x.ub))
                  for x in layer] for layer in routed_shape]
shape_polygon_length = [len(x) for x in shape_polygon]

via_polygon = [[Point(x.lb) for x in layer] for layer in routed_via]

via_table = [{} for _ in range(len(shape_polygon))]
for i in range(len(via_polygon)):
    for j in range(len(via_polygon[i])):
        via_table[i][len(shape_polygon[i])] = i, j
        shape_polygon[i].append(via_polygon[i][j])
        via_table[i + 1][len(shape_polygon[i + 1])] = i, j
        shape_polygon[i + 1].append(via_polygon[i][j])
via_table_inv = [{table[x]: x for x in table} for table in via_table]

net_components = [np.full(len(x), -1) for x in shape_polygon]
rtrees = [STRtree(layer) for layer in shape_polygon]


def dfs(layer, idx, net_id):
    net_components[layer][idx] = net_id
    for connect_idx in rtrees[layer].query(shape_polygon[layer][idx], predicate="intersects"):
        if net_components[layer][connect_idx] == - 1:
            if connect_idx in via_table[layer]:
                via_info = via_table[layer][connect_idx]
                net_components[layer][connect_idx] = net_id
                if via_info[0] == layer:
                    dfs(layer + 1, via_table_inv[layer + 1][via_info], net_id)
                elif via_info[0] == layer - 1:
                    # net_components[layer][connect_idx] = net_id
                    dfs(layer - 1, via_table_inv[layer - 1][via_info], net_id)
                else:
                    print(connect_idx, via_info, layer)
                    exit()
            else:
                dfs(layer, connect_idx, net_id)


net_id = 0
for layer in range(len(shape_polygon)):
    for idx, x in enumerate(shape_polygon[layer]):
        if net_components[layer][idx] == -1:
            dfs(layer, idx, net_id)
            net_id += 1

arrange_table = defaultdict(list)
for layer, table in enumerate(net_components):
    for i in range(shape_polygon_length[layer]):
        arrange_table[table[i]].append(routed_shape[layer][i])
for i in range(len(routed_via)):
    for j in range(len(routed_via[i])):
        arrange_table[net_components[i][via_table_inv[i][i, j]]].append(routed_via[i][j])

with open(fileout, "w") as f:
    print(net_id, file=f)
    for idx, (key, value) in enumerate(arrange_table.items()):
        print(f"C{idx+1}", file=f)
        for j in value:
            if not j.via:
                print("RoutedShape", j.layer,
                      f"{j.lb[0]}, {j.lb[1]}", f"{j.ub[0]}, {j.ub[1]}", file=f)
            else:
                print("RoutedVia", j.layer,
                      f"{j.lb[0]}, {j.lb[1]}", file=f)
