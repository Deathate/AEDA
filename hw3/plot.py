import plotly.graph_objects as go


def draw_placement(G):
    fig = go.Figure()
    for n in G.nodes:
        node = G.nodes[n]
        fig.add_shape(
            type="rect",
            x0=node["xy"][0],
            y0=node["xy"][1],
            x1=node["xy"][0] + node["w"],
            y1=node["xy"][1] + node["h"],
            line=dict(color="red", width=2),
            fillcolor="rgba(255, 0, 0, 0.1)",
        )
        fig.add_annotation(
            x=node["xy"][0] + node["w"] / 2,
            y=node["xy"][1] + node["h"] / 2,
            text=n,
            font=dict(size=8),
            showarrow=False,
        )

    fig.update_layout(
        margin=dict(l=20, r=20, b=10, t=10),
        xaxis=dict(scaleanchor="y", scaleratio=1),
        yaxis=dict(),
        xaxis_range=[-1, max(G.nodes[n]["xy"][0] + G.nodes[n]["w"] for n in G.nodes) + 1],
        yaxis_range=[-1, max(G.nodes[n]["xy"][1] + G.nodes[n]["h"] for n in G.nodes) + 1],
    )
    return fig
