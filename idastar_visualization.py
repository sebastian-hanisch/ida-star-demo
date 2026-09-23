"""Plotly-Abbildungen: Rasterkarte, Expansions-Mehrfachheit je Knoten (wie oft IDA* einen Knoten expandiert hat),
Expansionen je Iteration, Pfad-Überlagerung (IDA* liegt auf A*), Sweeps mit logarithmischer Achse. Achsen sind
gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht zoomen."""

import numpy as np
import plotly.graph_objects as go

NODE_COLOR = "#4c78a8"
BLOCKED_COLOR = "#9d755d"
ASTAR_COLOR = "#4c78a8"
IDA_COLOR = "#e45756"
UCS_COLOR = "#54a24b"


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height, legend_y=-0.1):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=legend_y), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _map_layout(fig, height=460):
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)
    return _base(fig, height)


def _start_goal_trace(inst):
    xy = inst.graph.xy
    return [
        go.Scatter(x=[xy[inst.start, 0]], y=[xy[inst.start, 1]], mode="markers", marker=dict(size=16, symbol="star", color="#2ca02c", line=dict(width=1, color="white")), name="Start"),
        go.Scatter(x=[xy[inst.goal, 0]], y=[xy[inst.goal, 1]], mode="markers", marker=dict(size=16, symbol="star", color="#d62728", line=dict(width=1, color="white")), name="Ziel"),
    ]


def _blocked_trace(inst):
    return go.Scatter(x=inst.blocked_xy[:, 0], y=inst.blocked_xy[:, 1], mode="markers", marker=dict(size=6, symbol="square", color=BLOCKED_COLOR), name="Hindernis")


def build_instance(inst):
    xy = inst.graph.xy
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xy[:, 0], y=xy[:, 1], mode="markers", marker=dict(size=6, color=NODE_COLOR, line=dict(width=1, color="white")), name="Offene Zellen"))
    if len(inst.blocked_xy):
        fig.add_trace(_blocked_trace(inst))
    fig.add_traces(_start_goal_trace(inst))
    return _map_layout(fig)


def build_multiplicity(inst, counts, astar_order):
    """Jeder Knoten, den IDA* expandiert hat, farbig nach der Zahl seiner Expansionen (logarithmische Skala); die
    von A* expandierten Knoten sind als Ring markiert - IDA* trifft (fast) dieselben Knoten, nur ungleich öfter."""
    xy = inst.graph.xy
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xy[:, 0], y=xy[:, 1], mode="markers", marker=dict(size=5, color="rgba(76,120,168,0.3)"), name="Nie expandiert", hoverinfo="skip"))
    if len(inst.blocked_xy):
        fig.add_trace(_blocked_trace(inst))
    if astar_order:
        idx = np.array(sorted(set(astar_order)))
        fig.add_trace(go.Scatter(x=xy[idx, 0], y=xy[idx, 1], mode="markers", marker=dict(size=15, color="rgba(0,0,0,0)", line=dict(width=1.5, color=ASTAR_COLOR)), name="Von A* expandiert", hoverinfo="skip"))
    if counts:
        nodes = np.array(sorted(counts))
        c = np.array([counts[n] for n in nodes], dtype=float)
        fig.add_trace(go.Scatter(x=xy[nodes, 0], y=xy[nodes, 1], mode="markers", marker=dict(size=9, color=np.log10(c), colorscale="YlOrRd", cmin=0, cmax=max(1.0, float(np.log10(c.max()))),
                      colorbar=dict(title="log10 Expansionen", thickness=12), line=dict(width=1, color="white")),
                      text=[f"{int(v)}x expandiert" for v in c], hovertemplate="%{text}<extra></extra>", name="Von IDA* expandiert"))
    fig.add_traces(_start_goal_trace(inst))
    return _map_layout(fig)


def build_iterations_bar(per_iteration):
    """Expansionen je Iteration (x = Nummer der Iteration; die Schwelle steht im Hover)."""
    xs = list(range(1, len(per_iteration) + 1))
    fig = go.Figure(go.Bar(x=xs, y=[e for _, e in per_iteration], marker_color=IDA_COLOR, customdata=[t for t, _ in per_iteration],
                           hovertemplate="Iteration %{x}<br>Schwelle %{customdata:.2f} km<br>%{y} Expansionen<extra></extra>"))
    fig.update_xaxes(title_text="Iteration (Schwelle steigt von h(Start) bis zu den optimalen Kosten)")
    fig.update_yaxes(title_text="Expansionen in dieser Iteration")
    return _base(fig, 320)


def build_paths(inst, ida_path, astar_path):
    xy = inst.graph.xy
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xy[:, 0], y=xy[:, 1], mode="markers", marker=dict(size=5, color="rgba(76,120,168,0.35)"), name="Zellen", hoverinfo="skip"))
    if len(inst.blocked_xy):
        fig.add_trace(_blocked_trace(inst))
    if astar_path:
        p = xy[astar_path]
        fig.add_trace(go.Scatter(x=p[:, 0], y=p[:, 1], mode="lines", line=dict(color="rgba(76,120,168,0.55)", width=9), name=f"A* ({len(astar_path)} Knoten)"))
    if ida_path:
        p = xy[ida_path]
        fig.add_trace(go.Scatter(x=p[:, 0], y=p[:, 1], mode="lines+markers", line=dict(color=IDA_COLOR, width=3, dash="dot"), marker=dict(size=5, color=IDA_COLOR), name=f"IDA* ({len(ida_path)} Knoten)"))
    fig.add_traces(_start_goal_trace(inst))
    return _map_layout(fig)


def build_sweep(rows, param_label, key, y_label, color=IDA_COLOR, log_y=False, marker_key=None):
    """Median als Linie, Minimum bis Maximum über die Instanzen als Band (`<key>_lo`/`<key>_hi`). Optional
    logarithmische y-Achse (Faktoren über mehrere Größenordnungen)."""
    xs = [r["value"] for r in rows]
    ys = [r[key] for r in rows]
    lo = [r[f"{key}_lo"] for r in rows]
    hi = [r[f"{key}_hi"] for r in rows]
    rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs + xs[::-1], y=hi + lo[::-1], mode="lines", fill="toself", fillcolor=f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.15)", line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", line=dict(color=color, width=2.5), name=y_label))
    fig.update_xaxes(title_text=param_label)
    fig.update_yaxes(title_text=y_label, type="log" if log_y else "linear")
    return _base(fig, 360, legend_y=-0.3)


def build_capped_share(rows, param_label):
    xs = [r["value"] for r in rows]
    fig = go.Figure(go.Bar(x=xs, y=[r["capped_share"] for r in rows], marker_color="#9d755d"))
    fig.update_xaxes(title_text=param_label, type="category")
    fig.update_yaxes(title_text="Abgebrochene Läufe (%)", range=[0, 100])
    return _base(fig, 300)
