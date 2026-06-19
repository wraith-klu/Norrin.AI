import plotly.graph_objects as go
import pandas as pd


def performance_history_chart(history: pd.DataFrame, prediction: float) -> go.Figure:
    chart = go.Figure()
    chart.add_trace(go.Scatter(x=history["match_date"], y=history["performance_metric"], name="Actual"))
    chart.add_hline(y=prediction, line_dash="dash", annotation_text="Next prediction")
    chart.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="Performance")
    return chart
