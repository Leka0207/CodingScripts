import shutil

import chess
import chess.engine
import plotly.graph_objects as go
import streamlit as st

ENGINE = shutil.which("stockfish") or "/usr/games/stockfish"  # apt puts it in /usr/games
LEVELS = {  # Stockfish skill level (0-20) + search limit
    "Easy": (0, chess.engine.Limit(depth=1)),
    "Medium": (6, chess.engine.Limit(depth=6)),
    "Hard": (20, chess.engine.Limit(time=1.0)),
}
GLYPH = dict(zip("PNBRQKpnbrqk", "♙♘♗♖♕♔♟♞♝♜♛♚"))
HEIGHT = dict(p=0.6, n=0.9, b=1.0, r=0.9, q=1.2, k=1.4)


def ai_move(board, level):
    skill, limit = LEVELS[level]
    with chess.engine.SimpleEngine.popen_uci(ENGINE) as engine:
        engine.configure({"Skill Level": skill})
        return engine.play(board, limit).move


def figure(board):
    # Board: 64 squares as a Mesh3d, 2 triangles each.
    vx, vy, i, j, k, colors = [], [], [], [], [], []
    for sq in chess.SQUARES:
        f, r, n = chess.square_file(sq), chess.square_rank(sq), len(vx)
        vx += [f, f + 1, f + 1, f]
        vy += [r, r, r + 1, r + 1]
        i += [n, n]; j += [n + 1, n + 2]; k += [n + 2, n + 3]
        colors += ["#b58863" if (f + r) % 2 == 0 else "#f0d9b5"] * 2
    traces = [go.Mesh3d(x=vx, y=vy, z=[0] * len(vx), i=i, j=j, k=k, facecolor=colors,
                        flatshading=True, hoverinfo="skip")]

    # Pieces: a stem per piece, ball on top, glyph above it (height = piece type).
    for color, fill, stem in ((chess.WHITE, "white", "#dddddd"), (chess.BLACK, "black", "#333333")):
        x, y, z, text, size = [], [], [], [], []
        for sq, piece in board.piece_map().items():
            if piece.color != color:
                continue
            cx, cy = chess.square_file(sq) + 0.5, chess.square_rank(sq) + 0.5
            x += [cx, cx, None]; y += [cy, cy, None]; z += [0, HEIGHT[piece.symbol().lower()], None]
            text += ["", GLYPH[piece.symbol()], ""]; size += [0, 12, 0]
        traces.append(go.Scatter3d(
            x=x, y=y, z=z, text=text, mode="lines+markers+text", textposition="top center",
            textfont=dict(size=26, color="#111"), line=dict(color=stem, width=9),
            marker=dict(size=size, color=fill, line=dict(color="black", width=2)), hoverinfo="skip"))

    axis = dict(showbackground=False, showgrid=False, zeroline=False, title="")
    fig = go.Figure(traces)
    fig.update_layout(
        height=650, margin=dict(l=0, r=0, t=0, b=0), showlegend=False, uirevision="keep-camera",
        scene=dict(
            aspectmode="manual", aspectratio=dict(x=1, y=1, z=0.35),
            xaxis=dict(axis, tickvals=[n + 0.5 for n in range(8)], ticktext=list("abcdefgh"), range=[0, 8]),
            yaxis=dict(axis, tickvals=[n + 0.5 for n in range(8)], ticktext=list("12345678"), range=[0, 8]),
            zaxis=dict(axis, visible=False, range=[0, 2]),
            camera=dict(eye=dict(x=0, y=-1.6, z=1.1)),
        ),
    )
    return fig


st.set_page_config("3D Chess", "♟", layout="wide")
st.sidebar.title("♟ 3D Chess")
level = st.sidebar.radio("AI difficulty", list(LEVELS), index=1)
if st.sidebar.button("New game") or "board" not in st.session_state:
    st.session_state.board = chess.Board()
board = st.session_state.board
st.sidebar.caption("Drag to rotate · scroll to zoom · you play White")

left, right = st.columns([3, 1])
left.plotly_chart(figure(board), width="stretch", key="board")

with right:
    if board.is_game_over():
        st.success(f"Game over: {board.result()} ({board.outcome().termination.name.replace('_', ' ').title()})")
    else:
        if board.is_check():
            st.warning("Check!")
        moves = {board.san(m): m for m in board.legal_moves}
        # key changes every ply, so a repeated position can't auto-replay the last pick
        san = st.selectbox("Your move", sorted(moves), index=None, placeholder="Pick a move…",
                           key=f"move-{len(board.move_stack)}")
        if san:
            board.push(moves[san])
            if not board.is_game_over():
                with st.spinner("AI thinking…"):
                    board.push(ai_move(board, level))
            st.rerun()
    st.text_area("Moves", chess.Board().variation_san(board.move_stack), height=300, disabled=True)
