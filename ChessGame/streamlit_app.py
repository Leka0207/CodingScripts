#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chess 3D -- Streamlit web app.

    pip install -r requirements.txt
    streamlit run streamlit_app.py

The board is rendered server side with Pillow and sent to the browser as an
image.  Streamlit reruns the whole script on every interaction, so there is no
60 fps loop here: one user gesture produces one redraw.  Dragging on the board
orbits the camera, clicking it picks a square by casting a ray from the
clicked pixel onto the board plane, exactly like the desktop build.
"""

import streamlit as st

st.set_page_config(page_title="Chess 3D", page_icon="\u265e", layout="wide")

import math
import time

import chess3d_core as core

try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    CLICKABLE = True
except Exception:
    CLICKABLE = False

BOARD_W, BOARD_H = 820, 620
QUALITY = {"Fast": 1.0, "Balanced": 1.5, "Sharp": 2.0}
TIME_SCALE = 0.6          # shared cloud CPUs are slower than a desktop
DRAG_PX = 7               # movement beyond this is a drag, not a click


# ---------------------------------------------------------------------------
#  cached resources
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_scene():
    """Piece meshes are built once per server process, not once per rerun."""
    return core.WebScene()


def make_viewport(yaw_deg, pitch_deg, dist):
    cam = core.Camera()
    cam.yaw = math.radians(yaw_deg)
    cam.pitch = math.radians(pitch_deg)
    cam.dist = dist
    vp = core.Viewport(BOARD_W, BOARD_H, cam)
    vp.prepare()
    return vp


def wrap180(a):
    while a > 180:
        a -= 360
    while a < -180:
        a += 360
    return a


# ---------------------------------------------------------------------------
#  state
# ---------------------------------------------------------------------------
def set_view(yaw, pitch, dist=None, rerun=True):
    st.session_state.cam_yaw = int(wrap180(yaw))
    st.session_state.cam_pitch = int(max(6, min(88, pitch)))
    if dist is not None:
        st.session_state.cam_dist = float(max(6.0, min(22.0, dist)))
    if rerun:
        st.rerun()


def new_game(mode="hvc", level="Medium", side="White"):
    human = core.WHITE if side == "White" else (
        core.BLACK if side == "Black" else
        (core.WHITE if int(time.time()) % 2 == 0 else core.BLACK))
    st.session_state.g = {
        "pos": core.Position(), "mode": mode, "level": level, "human": human,
        "selected": None, "targets": {}, "last": None, "promo": None,
        "log": [], "stack": [], "result": None, "result_text": "",
        "ai_info": "", "nonce": 0,
    }
    if mode == "hvc":
        set_view(-90 if human == core.WHITE else 90, 46, rerun=False)


def ensure_state():
    if "cam_yaw" not in st.session_state:
        st.session_state.cam_yaw = -90
        st.session_state.cam_pitch = 46
        st.session_state.cam_dist = 11.6
    if "g" not in st.session_state:
        new_game()


def refresh_status(g):
    code, text = g["pos"].status()
    g["result"] = None if code == "play" else code
    g["result_text"] = "" if code == "play" else text


def ai_to_move(g):
    return (g["mode"] == "hvc" and g["result"] is None
            and g["pos"].side != g["human"])


def human_to_move(g):
    return g["result"] is None and not ai_to_move(g)


def apply_move(g, move):
    pos = g["pos"]
    san = pos.san(move)
    if pos.side == core.WHITE:
        g["log"].append(["%d." % pos.fullmove, san, ""])
    elif g["log"] and g["log"][-1][2] == "":
        g["log"][-1][2] = san
    else:
        g["log"].append(["%d." % pos.fullmove, "...", san])
    pos.make(move)
    g["stack"].append(move)
    g["last"] = (move[0], move[1])
    g["selected"] = None
    g["targets"] = {}
    g["promo"] = None
    refresh_status(g)


def select(g, sq):
    pos = g["pos"]
    p = pos.board[sq]
    if p and (p >> 3) == pos.side and human_to_move(g):
        targets = {}
        for m in pos.legal_moves():
            if m[0] == sq:
                targets.setdefault(m[1], []).append(m)
        if targets:
            g["selected"] = sq
            g["targets"] = targets
            return True
    g["selected"] = None
    g["targets"] = {}
    return False


def click_square(g, sq):
    """True when the click changed something worth redrawing."""
    if sq is None or not human_to_move(g) or g["promo"]:
        return False
    if g["selected"] is not None and sq in g["targets"]:
        options = g["targets"][sq]
        if len(options) > 1:
            g["promo"] = options          # promotion: ask which piece
        else:
            apply_move(g, options[0])
        return True
    if sq == g["selected"]:
        g["selected"] = None
        g["targets"] = {}
        return True
    select(g, sq)
    return True


def undo(g):
    if not g["stack"]:
        return
    steps = 2 if (g["mode"] == "hvc" and len(g["stack"]) >= 2
                  and g["pos"].side == g["human"]) else 1
    for _ in range(steps):
        if not g["stack"]:
            break
        g["pos"].unmake(g["stack"].pop())
        if g["log"]:
            if g["log"][-1][2]:
                g["log"][-1][2] = ""
            else:
                g["log"].pop()
    g["selected"] = None
    g["targets"] = {}
    g["promo"] = None
    g["last"] = (g["stack"][-1][0], g["stack"][-1][1]) if g["stack"] else None
    refresh_status(g)


def captured_summary(pos):
    have = {core.WHITE: {}, core.BLACK: {}}
    for p in pos.board:
        if p:
            have[p >> 3][p & 7] = have[p >> 3].get(p & 7, 0) + 1
    taken = {core.WHITE: "", core.BLACK: ""}
    score = 0
    for col in (core.WHITE, core.BLACK):
        for t in (core.QUEEN, core.ROOK, core.BISHOP, core.KNIGHT, core.PAWN):
            missing = max(0, core.START_COUNTS[t] - have[col].get(t, 0))
            taken[col] += core.PIECE_LETTER[t] * missing
            score += (-1 if col == core.WHITE else 1) * core.PIECE_VALUE[t] * missing
    return taken, score


# ---------------------------------------------------------------------------
#  board widget
# ---------------------------------------------------------------------------
def show_board(img, key):
    """Render the board; returns (x1, y1, x2, y2) of the last gesture."""
    kwargs = dict(width=BOARD_W, key=key, click_and_drag=True)
    try:
        hit = streamlit_image_coordinates(img, image_format="JPEG",
                                          jpeg_quality=88, cursor="grab",
                                          **kwargs)
    except TypeError:                     # older component build
        hit = streamlit_image_coordinates(img, **kwargs)
    if not hit:
        return None
    if "x1" in hit:
        return (hit["x1"], hit["y1"], hit["x2"], hit["y2"])
    if "x" in hit:
        return (hit["x"], hit["y"], hit["x"], hit["y"])
    return None


def is_drag(gesture):
    """A gesture that travelled further than DRAG_PX is an orbit, not a tap."""
    x1, y1, x2, y2 = gesture
    return abs(x2 - x1) + abs(y2 - y1) > DRAG_PX


# ---------------------------------------------------------------------------
#  sidebar
# ---------------------------------------------------------------------------
def sidebar(g):
    with st.sidebar:
        st.title("\u265e Chess 3D")

        st.subheader("New game")
        opponent = st.radio("Opponent", ["Computer", "Another human"],
                            index=0 if g["mode"] == "hvc" else 1,
                            horizontal=True)
        mode = "hvc" if opponent == "Computer" else "hvh"
        level = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"],
                                 value=g["level"], disabled=(mode == "hvh"))
        st.caption(core.DIFFICULTY[level]["blurb"] if mode == "hvc"
                   else "Two players sharing one screen")
        side = st.radio("Play as", ["White", "Black", "Random"], index=0,
                        horizontal=True, disabled=(mode == "hvh"))
        if st.button("Start new game", type="primary", use_container_width=True):
            new_game(mode, level, side)
            st.rerun()

        st.divider()
        st.subheader("View")
        st.caption("Drag on the board to orbit, or use these.")
        c1, c2 = st.columns(2)
        if c1.button("White side", use_container_width=True):
            set_view(-90, 46)
        if c2.button("Black side", use_container_width=True):
            set_view(90, 46)
        c3, c4 = st.columns(2)
        if c3.button("Side on", use_container_width=True):
            set_view(0, 20)
        if c4.button("Top down", use_container_width=True):
            set_view(st.session_state.cam_yaw, 87)
        c5, c6 = st.columns(2)
        if c5.button("\u21ba 45\u00b0", use_container_width=True):
            set_view(st.session_state.cam_yaw - 45, st.session_state.cam_pitch)
        if c6.button("45\u00b0 \u21bb", use_container_width=True):
            set_view(st.session_state.cam_yaw + 45, st.session_state.cam_pitch)
        if st.button("Face the side to move", use_container_width=True):
            set_view(-90 if g["pos"].side == core.WHITE else 90, 46)

        st.slider("Rotate", -180, 180, key="cam_yaw")
        st.slider("Tilt", 6, 88, key="cam_pitch",
                  help="6\u00b0 is nearly eye level, 88\u00b0 is straight down")
        st.slider("Zoom", 6.0, 22.0, key="cam_dist", step=0.5)

        st.divider()
        quality = st.select_slider(
            "Image quality", list(QUALITY), value="Balanced",
            help="Sharper renders take the server longer")
        hints = st.toggle("Show move hints", value=True)
        coords = st.toggle("Show coordinates", value=True)
        return quality, hints, coords


# ---------------------------------------------------------------------------
#  main
# ---------------------------------------------------------------------------
def main():
    ensure_state()
    g = st.session_state.g
    quality, hints, coords = sidebar(g)
    scene = get_scene()

    # The computer moves before anything is drawn, so the board rendered
    # below already shows its reply.
    if ai_to_move(g):
        with st.spinner("Computer is thinking\u2026"):
            move, info = core.pick_move(g["pos"], g["level"], TIME_SCALE)
        if move is not None:
            apply_move(g, move)
            g["ai_info"] = info
        else:
            refresh_status(g)
        st.rerun()

    board_col, info_col = st.columns([3, 1.15], gap="medium")

    with board_col:
        if g["promo"]:
            st.warning("Pawn promotion \u2014 pick a piece")
            cols = st.columns(4)
            for col, (name, code) in zip(cols, (("Queen", core.QUEEN),
                                                ("Rook", core.ROOK),
                                                ("Bishop", core.BISHOP),
                                                ("Knight", core.KNIGHT))):
                if col.button(name, use_container_width=True):
                    for m in g["promo"]:
                        if m[2] == code:
                            apply_move(g, m)
                            break
                    g["nonce"] += 1
                    st.rerun()

        vp = make_viewport(st.session_state.cam_yaw,
                           st.session_state.cam_pitch,
                           st.session_state.cam_dist)
        pos = g["pos"]
        check_sq = pos.king_sq[pos.side] if pos.in_check() else None
        img = scene.render(vp, pos.board, BOARD_W, BOARD_H,
                           scale=QUALITY[quality], selected=g["selected"],
                           targets=list(g["targets"]), last_move=g["last"],
                           check_sq=check_sq, show_hints=hints,
                           show_coords=coords)

        if CLICKABLE:
            gesture = show_board(img, "board_%d" % g["nonce"])
            if gesture:
                x1, y1, x2, y2 = gesture
                if is_drag(gesture):
                    set_view(st.session_state.cam_yaw - (x2 - x1) * 0.38,
                             st.session_state.cam_pitch + (y2 - y1) * 0.28,
                             rerun=False)
                    changed = True
                else:
                    changed = click_square(g, scene.pick(vp, x2, y2))
                if changed:
                    g["nonce"] += 1
                    st.rerun()
            st.caption("Click a piece then a highlighted square to move. "
                       "Drag anywhere on the board to orbit the camera.")
        else:
            st.image(img)
            st.info("`streamlit-image-coordinates` is not installed, so the "
                    "board is display only. Use the move list below, or add "
                    "it to requirements.txt to click the board directly.")

        with st.expander("Move from a list (works everywhere, handy on phones)",
                         expanded=not CLICKABLE):
            if human_to_move(g) and not g["promo"]:
                choices = core.move_to_san_list(pos)
                picked = st.selectbox("Legal moves", [s for _, s in choices],
                                      label_visibility="collapsed")
                if st.button("Play move", use_container_width=True):
                    for m, s in choices:
                        if s == picked:
                            apply_move(g, m)
                            break
                    g["nonce"] += 1
                    st.rerun()
            else:
                st.caption("Not your turn.")

    with info_col:
        pos = g["pos"]
        if g["result"] == "checkmate":
            st.error(g["result_text"])
        elif g["result"]:
            st.info(g["result_text"])
        else:
            turn = "White" if pos.side == core.WHITE else "Black"
            if g["mode"] == "hvc":
                who = "you" if pos.side == g["human"] else "computer"
                st.subheader("%s to move (%s)" % (turn, who))
            else:
                st.subheader("%s to move" % turn)
            if pos.in_check():
                st.warning("Check!")

        if g["mode"] == "hvc":
            st.caption("Engine %s \u2014 %s" % (g["level"], g["ai_info"] or "-"))

        taken, score = captured_summary(pos)
        st.text("White took  %s" % (taken[core.BLACK] or "-"))
        st.text("Black took  %s" % (taken[core.WHITE] or "-"))
        if score:
            adv = ("%.1f" % (abs(score) / 100.0)).rstrip("0").rstrip(".")
            st.caption("Material: %s +%s" %
                       ("White" if score > 0 else "Black", adv))

        c1, c2 = st.columns(2)
        if c1.button("Take back", use_container_width=True,
                     disabled=not g["stack"]):
            undo(g)
            g["nonce"] += 1
            st.rerun()
        if c2.button("Restart", use_container_width=True):
            new_game(g["mode"], g["level"],
                     "White" if g["human"] == core.WHITE else "Black")
            st.rerun()

        st.markdown("**Moves**")
        if g["log"]:
            st.code("\n".join("%-4s %-8s %s" % (r[0], r[1], r[2])
                              for r in g["log"][-22:]), language=None)
        else:
            st.caption("No moves yet.")


if __name__ == "__main__":
    main()
