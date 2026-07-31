# Chess 3D — Streamlit web app

A rotatable 3D chess board rendered entirely in Python, playable in a browser.
Human vs human or human vs computer at three difficulty levels.

![files](https://img.shields.io/badge/deps-streamlit%20%7C%20numpy%20%7C%20pillow-blue)

## Files

| File | What it is |
|---|---|
| `streamlit_app.py` | The web front end. This is the entry point. |
| `chess3d_core.py` | Rules engine, search, 3D meshes, camera, Pillow renderer. No UI code. |
| `requirements.txt` | Dependencies. |
| `chess3d.py` | *(optional)* the original desktop pygame build. Not used by the web app. |

## Run it locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

It opens at <http://localhost:8501>.

## Deploy to Streamlit Community Cloud (free)

1. Put `streamlit_app.py`, `chess3d_core.py` and `requirements.txt` in a **public
   GitHub repo**, at the repo root.
2. Go to <https://share.streamlit.io> and sign in with GitHub.
3. **Create app → Deploy a public app from GitHub**, pick the repo and branch,
   and set **Main file path** to `streamlit_app.py`.
4. Deploy. First boot takes a couple of minutes while it installs the wheels.

No `packages.txt`, no Dockerfile, no system libraries needed — numpy and Pillow
are pure wheels and there is no SDL/OpenGL anywhere in the web build.

### Other hosts

The app is a plain Streamlit script, so it also runs unchanged on Hugging Face
Spaces (pick the *Streamlit* SDK), Render, Railway, or Fly.io. For a container:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.port=8501", "--server.address=0.0.0.0"]
```

## How to play

* **Click a piece**, then click one of the highlighted squares.
* **Drag anywhere on the board** to orbit the camera.
* The sidebar has preset angles, rotate/tilt/zoom sliders, difficulty, and
  which colour you play.
* **Move from a list** (expander under the board) is a keyboard-free fallback
  and works well on phones.

## How it works

Streamlit reruns the whole script on every interaction, so there is no render
loop. Each gesture produces exactly one redraw:

```
user gesture → rerun → apply move → computer replies → render PNG/JPEG → browser
```

The board is drawn by projecting mesh vertices through a pinhole camera and
filling polygons back-to-front with `PIL.ImageDraw` — the same geometry and
lighting as the desktop build, just a different rasteriser. Clicking works by
casting a ray from the clicked pixel onto the board plane and flooring the
result into a square index, so picking stays accurate at any camera angle.

## Performance notes

Measured on a modest cloud vCPU, per redraw:

| Image quality | Render time |
|---|---|
| Fast (1×) | ~26 ms |
| Balanced (1.5×, default) | ~63 ms |
| Sharp (2×) | ~93 ms |

Engine thinking time is scaled to 60% of the desktop budget (`TIME_SCALE` in
`streamlit_app.py`) because Community Cloud gives you a shared core: Easy is
near-instant, Medium ~1 s, Hard ~2.5 s. Raise it if you self-host on better
hardware.

Piece meshes are built once per server process via `@st.cache_resource`, and
game state lives in `st.session_state`, so every visitor gets their own board.

## Known limits of the Streamlit version

* **No continuous drag.** The camera updates once per drag gesture, not per
  frame — the browser sends the gesture, the server re-renders, the image comes
  back. It feels like a stepped orbit rather than the desktop's smooth one.
* **No auto-spin or move animations**, for the same reason.
* **The engine runs on the server.** Several simultaneous players on the free
  tier will queue behind each other on Hard. Lower `TIME_SCALE` if that bites.

If you want true 60 fps drag in a browser, the renderer would need to move
client-side (Three.js, or the Python engine compiled to WebAssembly via
Pyodide) — a different project. For turn-based chess, one redraw per move is
perfectly comfortable.
