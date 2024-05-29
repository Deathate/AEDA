# ./Lab3 [input file name] [output file name]

import sys
from dataclasses import dataclass
from functools import cached_property
from itertools import chain, combinations

import gurobipy as gp
import networkx as nx
import numpy as np
from gurobipy import GRB

from plot import *
from utility import *

if len(sys.argv) != 3:
    filein = "cases/ami33.block"
    # filein = "cases/ami49.block"
    # filein = "cases/apte.block"
    # filein = "cases/biasynth_2p4g.block"
    # filein = "cases/hp.block"
    # filein = "cases/lnamixbias_2p4g.block"
    fileout = "output.txt"
else:
    _, filein, fileout = sys.argv


@dataclass
class Node:
    name: str
    w: int
    h: int
    rotate: bool = False

    def __iter__(self):
        return iter([self])

    @cached_property
    def area(self):
        return self.w * self.h


class LBlock:
    def __init__(self, items: list[Node] = []):
        self.__items: list[Node] = items

    def __getitem__(self, i):
        return self.__items[i]


def solve_symmetry(node_query, symmetry_group):
    with gp.Model(env=env) as m:
        m.Params.LogToConsole = 0
        G = nx.Graph()
        for name in chain.from_iterable(symmetry_group):
            node = node_query[name]
            G.add_node(
                node.name,
                name=node.name,
                w=node.w,
                h=node.h,
                xy=m.addMVar(2, lb=0),
                rotate=node.rotate,
                area=node.area,
            )

        # add constraint to avoid overlapping
        for a, b in combinations(G.nodes, 2):
            n1d = G.nodes[a]
            n2d = G.nodes[b]
            cond1 = n1d["xy"][0] + n1d["w"] <= n2d["xy"][0]
            cond2 = n2d["xy"][0] + n2d["w"] <= n1d["xy"][0]
            cond3 = n1d["xy"][1] + n1d["h"] <= n2d["xy"][1]
            cond4 = n2d["xy"][1] + n2d["h"] <= n1d["xy"][1]

            z = m.addMVar(4, vtype=gp.GRB.BINARY)
            m.addConstr((z[0] == 1) >> cond1)
            m.addConstr((z[1] == 1) >> cond2)
            m.addConstr((z[2] == 1) >> cond3)
            m.addConstr((z[3] == 1) >> cond4)
            m.addConstr(gp.quicksum(z) == 1)
        middle_constraint = m.addVar()
        for group in symmetry_group:
            if len(group) == 2:
                n1d = G.nodes[group[0]]
                n2d = G.nodes[group[1]]
                m.addConstr(n1d["xy"][1] == n2d["xy"][1])
                m.addConstr(n1d["xy"][0] + n2d["xy"][0] + n1d["w"] == 2 * middle_constraint)
            else:
                n1d = G.nodes[group[0]]
                m.addConstr(n1d["xy"][0] + n1d["w"] / 2 == middle_constraint)

        # minimize the total area
        x_end = m.addMVar(len(G.nodes), lb=0)
        m.addConstrs(
            x_end[i] == G.nodes[n]["xy"][0] + G.nodes[n]["w"] for i, n in enumerate(G.nodes)
        )
        max_x = m.addVar()
        m.addConstr(max_x == gp.max_([x_end[i] for i in range(x_end.size)]), name="max_x")
        y_end = m.addMVar(len(G.nodes), lb=0)
        for i, n in enumerate(G.nodes):
            m.addConstr(y_end[i] == G.nodes[n]["xy"][1] + G.nodes[n]["h"])
        max_y = m.addVar()
        m.addConstr(max_y == gp.max_([y_end[i] for i in range(y_end.size)]), name="max_y")
        m.setObjective(max_x + max_y)

        m.optimize()
        assert m.Status == GRB.OPTIMAL
        for n in G.nodes:
            G.nodes[n]["xy"] = [float(x.X) for x in G.nodes[n]["xy"]]
        return G, float(max_x.X), float(max_y.X)


def solve_placement(block: LBlock):
    with gp.Model(env=env) as m:
        m.Params.LogToConsole = 0
        G = nx.Graph()
        for node in block:
            G.add_node(
                node.name,
                name=node.name,
                w=node.w,
                h=node.h,
                xy=m.addMVar(2, lb=0),
                rotate=node.rotate,
                area=node.area,
            )

        # add constraint to avoid overlapping
        bs = list(G.nodes(data=True))
        bs.sort(key=lambda x: x[1]["area"], reverse=True)
        for i, b in enumerate(bs):
            name = b[0]
            G.nodes[name]["order"] = i

        for i in range(1, len(bs)):
            for j in range(i - 1, -1, -1):
                n1d = bs[j][1]
                n2d = bs[i][1]
                cond1 = n1d["xy"][0] + n1d["w"] <= n2d["xy"][0]
                cond4 = n1d["xy"][1] + n1d["h"] <= n2d["xy"][1]

                z = m.addVar(vtype=gp.GRB.BINARY)
                m.addConstr((z == 1) >> cond1)
                m.addConstr((z == 0) >> cond4)
        # minimize the total area
        x_end = m.addMVar(len(G.nodes), lb=0)
        m.addConstrs(
            x_end[i] == G.nodes[n]["xy"][0] + G.nodes[n]["w"] for i, n in enumerate(G.nodes)
        )
        max_x = m.addVar()
        m.addConstr(max_x == gp.max_([x_end[i] for i in range(x_end.size)]), name="max_x")
        y_end = m.addMVar(len(G.nodes), lb=0)
        for i, n in enumerate(G.nodes):
            m.addConstr(y_end[i] == G.nodes[n]["xy"][1] + G.nodes[n]["h"])
        max_y = m.addVar()
        m.addConstr(max_y == gp.max_([y_end[i] for i in range(y_end.size)]), name="max_y")
        m.setObjective(max_x + max_y)

        total = sum([(b.w) * (b.h) for b in block])

        def rule(model, where):
            if where == GRB.Callback.MIPSOL:
                yvals = model.cbGetSolution(model._yvars)
                if total / (yvals[0] * yvals[1]) > 0.8:
                    model.terminate()

        m._yvars = [max_x, max_y]
        m.optimize(rule)
        assert m.Status == GRB.OPTIMAL or m.Status == 11
        for n in G.nodes:
            G.nodes[n]["xy"] = np.array([float(x.X) for x in G.nodes[n]["xy"]])
        return G


def read_file(input_path):
    num_blocks = 0
    nodes = []
    symmetry_groups = []
    with open(input_path, "r") as file:
        for line in file.readlines():
            line = line.strip()
            if line:
                if line.startswith("NumBlocks"):
                    num_blocks = int(line.split()[1])
                elif len(nodes) < num_blocks:
                    name, w, h = line.split()
                    nodes.append(Node(name, float(w), float(h)))
                else:
                    if line.startswith("Symmetry Group"):
                        symmetry_groups.append([])
                    elif symmetry_groups:
                        symmetry_groups[-1].append(line.split())
    return nodes, symmetry_groups


nodes, symmetry_groups = read_file(filein)
sym_relation = set(list(chain.from_iterable((chain.from_iterable(symmetry_groups)))))
node_query = {node.name: node for node in nodes}
sym_blocks = []
sym_results = []
for symmetry_group in symmetry_groups:
    for group in symmetry_group:
        if len(group) == 2:
            if node_query[group[0]].w != node_query[group[1]].w:
                node_query[group[1]].rotate = True
                node_query[group[1]].w, node_query[group[1]].h = (
                    node_query[group[1]].h,
                    node_query[group[1]].w,
                )
    sym_blocks.append(Node(",".join(chain.from_iterable(symmetry_group)), 0, 0))
blocks = LBlock([node for node in nodes if node.name not in sym_relation] + sym_blocks)
with HiddenPrints():
    options = {
        "WLSACCESSID": "d86975f0-77a0-4932-a08b-714ed42dcf09",
        "WLSSECRET": "77712e41-0f33-48ea-babf-9cd37b75a30c",
        "LICENSEID": 2519992,
    }
    with gp.Env(params=options) as env:
        for i, symmetry_group in enumerate(symmetry_groups):
            G, width, height = solve_symmetry(node_query, symmetry_group)
            sym_blocks[i].w, sym_blocks[i].h = width, height
            sym_results.append(G)
        G = solve_placement(blocks)
for symmetry_group, sym_result in zip(symmetry_groups, sym_results):
    symmetry_group_flatten = list(chain.from_iterable(symmetry_group))
    name = ",".join(symmetry_group_flatten)
    for bname in symmetry_group_flatten:
        node = sym_result.nodes[bname]
        G.add_node(
            bname,
            name=bname,
            w=node["w"],
            h=node["h"],
            xy=node["xy"] + G.nodes[name]["xy"],
            rotate=node["rotate"],
            area=node["area"],
        )
    G.remove_node(name)
# draw_placement(G).show()
with open(fileout, "w") as file:
    for n in G.nodes:
        node = G.nodes[n]
        # <Module Name> <(x, y)> <R0 or R90>
        file.write(
            f"{node['name']} ({int(round(node['xy'][0],0))}, {int(round(node['xy'][1],0))}) {'R0' if not node['rotate'] else 'R90'}\n"
        )
