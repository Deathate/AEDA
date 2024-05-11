import copy
from datetime import datetime
from pathlib import Path

import numpy as np
import plotly
import plotly.graph_objects as go
import shapely


class PlotlyUtility:
    def __init__(self, ratio=1, update_layout=False, height=800):
        self.fig = go.Figure()
        self.fig.update_yaxes(
            scaleanchor="x",
            scaleratio=ratio,
        )
        if update_layout:
            self.fig.update_layout(
                autosize=False,
                margin=dict(l=0, r=0, t=0, b=0),
                height=height,
            )
        self.fig.update_layout(showlegend=False)
        # self.fig.update_yaxes(automargin=True)
        self.color_list = plotly.colors.DEFAULT_PLOTLY_COLORS
        self.color_id = 0
        self.buffer_template = [[], [], {"color": None,
                                         "text": [[], [], []], "label": [[], [], []]}]
        self.buffer = [copy.deepcopy(self.buffer_template)]
        self.change_group(0)

    def add_rectangle(self, coord, text="", label="", color_id=None):
        if isinstance(coord, shapely.Polygon):
            coord = shapely.get_coordinates(coord)
        if coord.size == 0:
            return
        x = coord[:, 0]
        y = coord[:, 1]
        # self.fig.add_annotation(
        #     x=(x.min() + x.max()) / 2,
        #     y=y.min(),
        #     text=text,
        #     showarrow=False,
        # )
        self.buffer[self.buffer_id][0].extend(x.tolist())
        self.buffer[self.buffer_id][1].extend(y.tolist())
        self.buffer[self.buffer_id][0].append(None)
        self.buffer[self.buffer_id][1].append(None)
        if color_id is None:
            color_id = self.color_id
        self.buffer[self.buffer_id][2]["color"] = self.color_list[color_id]
        text = str(text)
        label = str(label)
        self.buffer[self.buffer_id][2]["text"][0].append((x.min() + x.max()) / 2)
        self.buffer[self.buffer_id][2]["text"][1].append(y.min())
        self.buffer[self.buffer_id][2]["text"][2].append(text)
        self.buffer[self.buffer_id][2]["label"][0].append((x.min() + x.max()) / 2)
        self.buffer[self.buffer_id][2]["label"][1].append((y.min() + y.max()) / 2)
        self.buffer[self.buffer_id][2]["label"][2].append(label)

    def change_group(self, i):
        self.buffer_id = i
        if len(self.buffer) <= i:
            for _ in range(i - len(self.buffer) + 1):
                self.buffer.append(copy.deepcopy(self.buffer_template))

    def change_color(self):
        self.color_id += 1
        self.color_id %= len(self.color_list)
        self.buffer.append(copy.deepcopy(self.buffer_template))
        self.buffer_id = len(self.buffer) - 1

    def show(self, save=False):
        for b in self.buffer:
            if len(b[0]) > 0:
                self.fig.add_trace(
                    go.Scatter(
                        x=b[0],
                        y=b[1],
                        mode="lines",
                        fill="toself",
                        line=dict(color=b[2]["color"]),
                        hoverinfo="none",
                    ))

                self.fig.add_scatter(
                    x=b[2]["label"][0],
                    y=b[2]["label"][1],
                    mode="none",
                    text=b[2]["label"][2],
                    hoverinfo="text"
                )
                text_property = np.array((b[2]["text"][0], b[2]["text"][1], b[2]["text"][2])).T
                text_property = text_property[text_property[:, 2] != ""]
                self.fig.add_trace(go.Scatter(
                    x=text_property[:, 0],
                    y=text_property[:, 1],
                    mode="markers+text",
                    # name="Lines, Markers and Text",
                    text=text_property[:, 2],
                    textposition="top center",
                    hoverinfo="x+y",
                ))
        if save:
            # current_time_seconds = time.time()
            readable_time = datetime.now()
            Path("images").mkdir(parents=True, exist_ok=True)
            self.fig.write_image(f"images/{readable_time}.png")
        else:
            self.fig.show()
