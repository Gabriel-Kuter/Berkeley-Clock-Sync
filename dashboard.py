import dash
from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import os
import time
from datetime import datetime
import math
import pandas as pd

PROCESSOS = sorted(
    [
        f.split("_")[1].split(".")[0]
        for f in os.listdir(".")
        if f.startswith("offset_") and f.endswith(".txt")
    ]
)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SLATE])
app.title = "Painel Berkeley Avançado"


def obter_offset(pid):
    try:
        with open(f"offset_{pid}.txt", "r") as f:
            return float(f.read().strip())
    except:
        return None


def formatar_horario(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")


def gerar_ponteiros_analogicos(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    h = dt.hour % 12
    m = dt.minute
    s = dt.second

    ang_h = (h + m / 60) * 30
    ang_m = m * 6
    ang_s = s * 6

    def ang_para_xy(angulo, tamanho):
        rad = math.radians(angulo - 90)
        return (tamanho * math.cos(rad), tamanho * math.sin(rad))

    # Ponteiros
    hx, hy = ang_para_xy(ang_h, 0.4)
    mx, my = ang_para_xy(ang_m, 0.6)
    sx, sy = ang_para_xy(ang_s, 0.9)

    # Números do mostrador
    numeros = []
    for i in range(1, 13):
        x, y = ang_para_xy(i * 30, 1.0)
        numeros.append(
            go.Scatter(
                x=[x],
                y=[y],
                mode="text",
                text=[str(i)],
                textfont=dict(color="white", size=14),
                showlegend=False,
            )
        )

    fig = go.Figure()

    # Números
    for n in numeros:
        fig.add_trace(n)

    # Ponteiros
    fig.add_trace(
        go.Scatter(
            x=[0, hx], y=[0, hy], mode="lines", line=dict(width=5, color="white")
        )
    )
    fig.add_trace(
        go.Scatter(x=[0, mx], y=[0, my], mode="lines", line=dict(width=3, color="blue"))
    )
    fig.add_trace(
        go.Scatter(x=[0, sx], y=[0, sy], mode="lines", line=dict(width=1, color="red"))
    )

    fig.update_layout(
        showlegend=False,
        xaxis=dict(
            range=[-1.2, 1.2], showgrid=False, zeroline=False, showticklabels=False
        ),
        yaxis=dict(
            range=[1.2, -1.2], showgrid=False, zeroline=False, showticklabels=False
        ),  # inverte o Y
        margin=dict(l=30, r=30, t=60, b=100),
        plot_bgcolor="black",
        paper_bgcolor="black",
    )

    return fig


def construir_card(pid, agora, offset):
    if offset is None:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H5(f"{pid} ❌", className="card-title"),
                    html.P("Aguardando conexão..."),
                ]
            ),
            color="secondary",
            inverse=True,
        )

    ajustado = agora + offset
    delta = abs(agora - ajustado)
    cor = "success" if delta <= 0.05 else "danger"

    return dbc.Card(
        [
            dbc.CardHeader(html.H5(f"Processo {pid}")),
            dbc.CardBody(
                [
                    html.Div(f"⏰ {formatar_horario(ajustado)}", className="fs-4"),
                    html.Div(f"offset: {offset:+.3f}s | Δ: {delta:.3f}s"),
                    dcc.Graph(
                        figure=gerar_ponteiros_analogicos(ajustado),
                        config={"displayModeBar": False},
                    ),
                ]
            ),
        ],
        color=cor,
        inverse=True,
    )


def gerar_grafico_geral():
    fig = go.Figure()
    cores = [
        "#00BFFF",  # azul claro
        "#FF69B4",  # rosa choque
        "#FFD700",  # amarelo ouro
        "#7CFC00",  # verde-limão
        "#FF4500",  # laranja avermelhado
        "#9A32CD",  # roxo médio
        "#40E0D0",  # turquesa
        "#FF1493",  # rosa profundo
        "#00FA9A",  # verde médio
        "#DC143C",  # vermelho cereja
    ]  # Uma cor por processo

    for i, pid in enumerate(PROCESSOS):
        try:
            df = pd.read_csv(f"offset_{pid}.csv")
            fig.add_trace(
                go.Scatter(
                    x=df["cycle"],
                    y=df["offset"],
                    mode="lines+markers",
                    name=pid,
                    line=dict(color=cores[i % len(cores)]),
                )
            )
        except:
            continue

    fig.update_layout(
        title="Convergência dos Offsets",
        xaxis_title="Ciclo de Sincronização",
        yaxis_title="Offset acumulado (s)",
        font=dict(color="white"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin=dict(l=30, r=30, t=40, b=40),
        legend=dict(
            orientation="h",
            x=0.5,
            y=-0.25,
            xanchor="center",
            yanchor="top",
            bgcolor="rgba(0,0,0,0)",  # transparente
        ),
    )
    return fig


# Layout geral do dashboard
app.layout = dbc.Container(
    [
        html.H1(
            "🛰️ Painel de Sincronização - Algoritmo de Berkeley",
            className="my-4 text-info text-center",
        ),
        html.Div(id="relogio-coordenador", className="fs-4 text-center mb-4"),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "🔄 Resetar Simulação",
                        id="botao-resetar",
                        color="danger",
                        className="mb-4",
                    ),
                    width="auto",
                )
            ],
            justify="center",
        ),
        html.Div(id="mensagem-reset", className="text-success text-center mb-4"),
        dbc.Row(id="cards-processos", justify="center"),
        dcc.Interval(id="intervalo-atualizacao", interval=1000, n_intervals=0),
        html.Hr(),
        dcc.Graph(id="grafico-geral", config={"displayModeBar": False}),
    ],
    fluid=True,
)


@app.callback(
    Output("relogio-coordenador", "children"),
    Output("cards-processos", "children"),
    Output("grafico-geral", "figure"),
    Input("intervalo-atualizacao", "n_intervals"),
)
def atualizar_painel(n):
    agora = time.time()
    cards = []
    for pid in PROCESSOS:
        offset = obter_offset(pid)
        card = dbc.Col(construir_card(pid, agora, offset), width=4)
        cards.append(card)

    return (
        f"Relógio do Coordenador: {formatar_horario(agora)}",
        cards,
        gerar_grafico_geral(),
    )


# Reset da simulação
@app.callback(
    Output("mensagem-reset", "children"),
    Input("botao-resetar", "n_clicks"),
    prevent_initial_call=True,
)
def resetar_simulacao(n):
    count = 0
    for pid in PROCESSOS:
        for ext in [".txt", ".csv"]:
            try:
                os.remove(f"offset_{pid}{ext}")
                count += 1
            except:
                continue
    return f"✅ Simulação resetada ({count} arquivos apagados)."


if __name__ == "__main__":
    app.run(debug=True)
