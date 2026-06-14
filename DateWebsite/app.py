import streamlit as st
from datetime import date, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import streamlit.components.v1 as components

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="A Special Invitation 💌",
    page_icon="💌",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Lato:wght@300;400&display=swap');

  html, body, [data-testid="stAppViewContainer"] { background: #0d0a0f !important; }
  [data-testid="stAppViewContainer"] {
    background:
      radial-gradient(ellipse 80% 60% at 50% 0%, rgba(180,60,120,0.18) 0%, transparent 70%),
      radial-gradient(ellipse 60% 40% at 80% 100%, rgba(120,40,160,0.14) 0%, transparent 60%),
      #0d0a0f !important;
  }
  [data-testid="stHeader"], footer { display: none !important; }
  [data-testid="stSidebar"] { display: none !important; }
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(200,100,160,0.3); border-radius: 2px; }

  .block-container { max-width: 680px !important; padding: 3rem 2rem 4rem !important; margin: 0 auto; }
  * { font-family: 'Lato', sans-serif; color: #f0e8f0; }
  h1, h2, h3 { font-family: 'Cormorant Garamond', serif !important; font-weight: 300 !important; letter-spacing: 0.02em; }

  .hero-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(180,60,120,0.08) 100%);
    border: 1px solid rgba(200,100,160,0.25); border-radius: 24px; padding: 3rem 2.5rem;
    text-align: center; box-shadow: 0 8px 48px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.07);
    backdrop-filter: blur(12px); animation: fadeUp 0.9s ease both;
  }
  .stage-card {
    background: linear-gradient(160deg, rgba(255,255,255,0.04) 0%, rgba(120,40,160,0.06) 100%);
    border: 1px solid rgba(180,80,140,0.2); border-radius: 20px; padding: 2.5rem 2rem;
    text-align: center; box-shadow: 0 4px 32px rgba(0,0,0,0.4); animation: fadeUp 0.7s ease both;
  }
  .headline {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: clamp(2.2rem, 6vw, 3.2rem) !important; font-weight: 300 !important;
    line-height: 1.15 !important; color: #f8e8f4 !important; margin-bottom: 0.4rem !important;
  }
  .headline em { font-style: italic; color: #e8a0c8; }
  .subhead {
    font-size: 0.95rem; color: rgba(220,180,210,0.7); font-weight: 300;
    letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2rem;
  }
  .body-text { font-size: 1.05rem; color: rgba(240,220,240,0.85); line-height: 1.75; font-weight: 300; }
  .petal-row { font-size: 1.6rem; letter-spacing: 0.3rem; margin: 1rem 0; opacity: 0.7; }
  .divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(200,100,160,0.4), transparent); margin: 1.8rem 0; }

  .step-indicator { display: flex; justify-content: center; gap: 0.6rem; margin-bottom: 2rem; }
  .step-dot { width: 8px; height: 8px; border-radius: 50%; background: rgba(180,80,140,0.25); border: 1px solid rgba(180,80,140,0.4); display: inline-block; }
  .step-dot.active { background: #d060a0; box-shadow: 0 0 10px rgba(200,80,160,0.6); border-color: #d060a0; }
  .step-dot.done { background: rgba(200,100,160,0.5); border-color: rgba(200,100,160,0.6); }

  div[data-testid="stButton"] > button {
    border-radius: 50px !important; font-family: 'Lato', sans-serif !important; font-weight: 400 !important;
    letter-spacing: 0.1em !important; font-size: 0.88rem !important; text-transform: uppercase !important;
    padding: 0.7rem 2.2rem !important; transition: all 0.25s ease !important; border: none !important;
  }
  div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #c04080, #8020b0) !important; color: #fff !important;
    box-shadow: 0 4px 20px rgba(180,60,140,0.45) !important;
  }
  div[data-testid="stButton"] > button[kind="primary"]:hover {
    transform: translateY(-2px) scale(1.03) !important; box-shadow: 0 8px 28px rgba(180,60,140,0.6) !important;
  }
  div[data-testid="stButton"] > button[kind="secondary"] {
    background: transparent !important; border: 1px solid rgba(200,100,160,0.35) !important; color: rgba(220,170,200,0.8) !important;
  }
  div[data-testid="stButton"] > button[kind="secondary"]:hover {
    border-color: rgba(200,100,160,0.7) !important; color: #e8b0d0 !important; transform: translateY(-1px) !important;
  }

  .option-btn > button {
    background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(180,80,140,0.25) !important;
    color: rgba(235,205,225,0.9) !important; border-radius: 16px !important; padding: 1rem 0.8rem !important;
    font-size: 0.85rem !important; letter-spacing: 0.06em !important; width: 100% !important; transition: all 0.2s ease !important;
  }
  .option-btn > button:hover { background: rgba(180,60,140,0.18) !important; border-color: rgba(200,100,160,0.55) !important; transform: translateY(-2px) !important; }
  .option-btn-selected > button {
    background: linear-gradient(135deg, rgba(180,50,130,0.45), rgba(100,30,150,0.45)) !important;
    border: 1px solid rgba(210,100,170,0.7) !important; color: #f8e0f0 !important; box-shadow: 0 0 18px rgba(180,60,140,0.35) !important;
  }

  /* Location option buttons — full width, left-aligned, slightly taller */
  .loc-btn > button {
    background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(180,80,140,0.22) !important;
    color: rgba(235,205,225,0.88) !important; border-radius: 14px !important;
    padding: 1rem 1.3rem !important; font-size: 0.9rem !important;
    letter-spacing: 0.03em !important; width: 100% !important;
    text-align: left !important; transition: all 0.2s ease !important; margin-bottom: 0.1rem !important;
  }
  .loc-btn > button:hover {
    background: rgba(160,50,120,0.16) !important; border-color: rgba(200,90,160,0.5) !important;
    transform: translateX(4px) !important;
  }
  .loc-btn-selected > button {
    background: linear-gradient(135deg, rgba(180,50,130,0.4), rgba(100,30,150,0.38)) !important;
    border: 1px solid rgba(210,100,170,0.65) !important; color: #f8e0f0 !important;
    box-shadow: 0 0 16px rgba(180,60,140,0.28) !important; transform: translateX(4px) !important;
  }

  div[data-testid="stDateInput"] input {
    background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(180,80,140,0.3) !important;
    border-radius: 12px !important; color: #f0e0f0 !important; padding: 0.6rem 1rem !important;
  }

  .final-card {
    background: linear-gradient(145deg, rgba(180,50,110,0.15) 0%, rgba(100,20,140,0.15) 100%);
    border: 1px solid rgba(200,100,160,0.4); border-radius: 28px; padding: 3.5rem 2.5rem 2rem;
    text-align: center; box-shadow: 0 0 60px rgba(180,60,130,0.2), 0 8px 48px rgba(0,0,0,0.5);
    animation: fadeUp 0.9s ease both;
  }
  .final-headline {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: clamp(1.9rem, 5.5vw, 2.8rem) !important; font-weight: 400 !important;
    font-style: italic !important; color: #f4d0e8 !important; line-height: 1.2 !important; margin-bottom: 0.5rem !important;
  }
  .summary-item {
    display: flex; align-items: center; gap: 0.8rem;
    background: rgba(255,255,255,0.04); border: 1px solid rgba(180,80,140,0.18);
    border-radius: 12px; padding: 0.85rem 1.2rem; margin: 0.5rem 0;
    text-align: left; font-size: 0.95rem; color: rgba(235,210,230,0.9);
  }

  .no-card {
    background: linear-gradient(145deg, rgba(60,20,80,0.4) 0%, rgba(20,10,30,0.4) 100%);
    border: 1px solid rgba(120,60,100,0.3); border-radius: 20px; padding: 3rem 2rem;
    text-align: center; animation: fadeUp 0.7s ease both;
  }

  .time-slot > button {
    background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(180,80,140,0.25) !important;
    color: rgba(230,200,220,0.85) !important; border-radius: 12px !important; width: 100% !important;
    padding: 0.65rem !important; font-size: 0.9rem !important; letter-spacing: 0.04em !important;
  }
  .time-slot > button:hover { background: rgba(160,50,120,0.2) !important; border-color: rgba(200,90,160,0.5) !important; }
  .time-slot-selected > button {
    background: linear-gradient(135deg, rgba(180,50,130,0.5), rgba(100,30,150,0.4)) !important;
    border: 1px solid rgba(210,100,170,0.65) !important; color: #f8e0f0 !important; box-shadow: 0 0 14px rgba(180,60,140,0.3) !important;
  }

  /* Notes textarea */
  div[data-testid="stTextArea"] textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(180,80,140,0.3) !important;
    border-radius: 14px !important; color: #f0e0f0 !important;
    font-family: 'Lato', sans-serif !important; font-size: 0.95rem !important;
    line-height: 1.65 !important; padding: 1rem !important;
    resize: vertical !important;
  }
  div[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(200,90,160,0.6) !important;
    box-shadow: 0 0 0 2px rgba(180,60,140,0.15) !important;
  }
  div[data-testid="stTextArea"] label { color: rgba(210,175,200,0.7) !important; font-size: 0.82rem !important; letter-spacing: 0.07em !important; text-transform: uppercase !important; }

  /* Success / error banners */
  .email-success {
    background: rgba(40,160,100,0.15); border: 1px solid rgba(60,200,120,0.35);
    border-radius: 12px; padding: 0.9rem 1.2rem; text-align: center; margin: 1rem 0;
    color: rgba(160,240,200,0.9); font-size: 0.9rem;
  }
  .email-error {
    background: rgba(180,40,60,0.15); border: 1px solid rgba(220,80,100,0.35);
    border-radius: 12px; padding: 0.9rem 1.2rem; text-align: center; margin: 1rem 0;
    color: rgba(240,160,175,0.9); font-size: 0.9rem;
  }

  @keyframes fadeUp { from { opacity: 0; transform: translateY(28px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes pulse-glow { 0%, 100% { text-shadow: 0 0 12px rgba(220,100,170,0.4); } 50% { text-shadow: 0 0 28px rgba(220,100,170,0.8), 0 0 50px rgba(180,60,140,0.4); } }
  @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-6px); } }

  .float-icon { display: inline-block; animation: float 3s ease-in-out infinite; font-size: 3rem; }
  .glow-text { animation: pulse-glow 2.5s ease-in-out infinite; }
</style>
""", unsafe_allow_html=True)

# ── Session State Init ─────────────────────────────────────────────────────
defaults = {
    "stage": 0,
    "her_name": "",
    "chosen_time": None,
    "chosen_date": None,
    "chosen_location": None,
    "chosen_vibes": [],
    "her_notes": "",
    "email_sent": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

TOTAL_STAGES = 6

def step_dots(current: int):
    dots = ""
    for i in range(1, TOTAL_STAGES + 1):
        cls = "done" if i < current else ("active" if i == current else "")
        dots += f'<span class="step-dot {cls}"></span>'
    st.markdown(f'<div class="step-indicator">{dots}</div>', unsafe_allow_html=True)


# ── Email Sender ───────────────────────────────────────────────────────────
def send_date_results_email(name_str, date_str, time_str, location_str, vibes_str, notes_str):
    """Send results to Anthony's email via Gmail SMTP."""
    try:
        cfg = st.secrets["email"]
        sender    = cfg["sender_address"]
        password  = cfg["app_password"]
        recipient = cfg["recipient_address"]

        display_name = name_str if name_str.strip() else "She"
        subject_name = name_str.strip() if name_str.strip() else "Her"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"💌 {subject_name} Said YES — Date Details Inside"
        msg["From"]    = sender
        msg["To"]      = recipient

        plain = f"""
{display_name} said YES! Here are the date details:

👤  Name:     {name_str if name_str.strip() else '(not provided)'}
📅  Date:     {date_str}
⏰  Time:     {time_str}
📍  Location: {location_str}
✨  Vibe:     {vibes_str}
💬  Notes:    {notes_str if notes_str.strip() else '(none)'}

Go get her! 🌹
"""

        html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ margin:0; padding:0; background:#0d0a0f; font-family:'Georgia',serif; }}
  .wrapper {{ max-width:560px; margin:40px auto; background:linear-gradient(160deg,#1a0e20,#120818);
    border:1px solid rgba(200,100,160,0.3); border-radius:20px; overflow:hidden; }}
  .header {{ padding:36px 32px 24px; text-align:center;
    background:linear-gradient(135deg,rgba(180,50,120,0.25),rgba(100,20,150,0.2)); }}
  .emoji-big {{ font-size:48px; display:block; margin-bottom:12px; }}
  h1 {{ margin:0; font-size:28px; font-weight:400; font-style:italic; color:#f4d0e8;
    letter-spacing:0.02em; }}
  .body {{ padding:28px 32px 32px; }}
  .row {{ display:flex; align-items:flex-start; gap:14px; background:rgba(255,255,255,0.04);
    border:1px solid rgba(180,80,140,0.18); border-radius:12px;
    padding:14px 18px; margin:10px 0; }}
  .row-icon {{ font-size:22px; margin-top:2px; flex-shrink:0; }}
  .row-label {{ font-size:11px; text-transform:uppercase; letter-spacing:0.1em;
    color:rgba(200,155,185,0.6); margin-bottom:3px; }}
  .row-value {{ font-size:15px; color:#f0d8f0; }}
  .notes-box {{ background:rgba(180,50,130,0.1); border:1px solid rgba(200,90,160,0.25);
    border-radius:12px; padding:16px 18px; margin:14px 0 0; }}
  .notes-label {{ font-size:11px; text-transform:uppercase; letter-spacing:0.1em;
    color:rgba(200,155,185,0.6); margin-bottom:6px; }}
  .notes-text {{ font-size:14px; color:rgba(235,210,230,0.85); line-height:1.7; font-style:italic; }}
  .footer {{ text-align:center; padding:20px 32px 28px; border-top:1px solid rgba(180,80,140,0.15); }}
  .footer p {{ margin:0; font-size:13px; color:rgba(200,155,180,0.5); font-style:italic; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <span class="emoji-big">💌</span>
    <h1>{display_name} said yes — and here's the plan</h1>
  </div>
  <div class="body">
    <div class="row">
      <div class="row-icon">👤</div>
      <div><div class="row-label">Name</div><div class="row-value">{name_str if name_str.strip() else '—'}</div></div>
    </div>
    <div class="row">
      <div class="row-icon">🗓</div>
      <div><div class="row-label">Date</div><div class="row-value">{date_str}</div></div>
    </div>
    <div class="row">
      <div class="row-icon">⏰</div>
      <div><div class="row-label">Time</div><div class="row-value">{time_str}</div></div>
    </div>
    <div class="row">
      <div class="row-icon">📍</div>
      <div><div class="row-label">Location Vibe</div><div class="row-value">{location_str}</div></div>
    </div>
    <div class="row">
      <div class="row-icon">✨</div>
      <div><div class="row-label">Vibe</div><div class="row-value">{vibes_str}</div></div>
    </div>
    {"" if not notes_str.strip() else f'''
    <div class="notes-box">
      <div class="notes-label">💬 Her Notes</div>
      <div class="notes-text">{notes_str.replace(chr(10), "<br>")}</div>
    </div>
    '''}
  </div>
  <div class="footer"><p>Now go make it the best date ever. 🌹</p></div>
</div>
</body>
</html>
"""

        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())

        return True, None
    except KeyError:
        return False, "secrets_missing"
    except Exception as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 0 — The Invitation
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.stage == 0:
    st.markdown("""
    <div class="hero-card">
      <div class="float-icon">💌</div>
      <div style="margin-top:1.2rem">
        <p class="subhead">A personal invitation</p>
        <h1 class="headline">I have a question<br>for <em>you</em>…</h1>
      </div>
      <div class="divider"></div>
      <p class="body-text">
        There's someone I've been thinking about — and that someone is you.<br>
        I'd really love the chance to take you out and show you a genuinely great time.<br><br>
        So here's my ask:
      </p>
      <div class="divider"></div>
      <p style="font-family:'Cormorant Garamond',serif; font-size:1.5rem; font-style:italic; color:#e8b0d0; margin-bottom:1.8rem;">
        Will you go on a date with me? 🌹
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Yes! 🥰", type="primary", use_container_width=True):
                st.session_state.stage = 1
                st.rerun()
        with col_no:
            if st.button("No…", type="secondary", use_container_width=True):
                st.session_state.stage = -1
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STAGE -1 — Said No
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == -1:
    st.markdown("""
    <div class="no-card">
      <div style="font-size:3rem; margin-bottom:1rem;">🥺</div>
      <h2 style="font-family:'Cormorant Garamond',serif; font-size:2rem; font-weight:300; color:#c090b0; margin-bottom:1rem;">
        Oh… that stings a little.
      </h2>
      <p class="body-text" style="color:rgba(210,175,200,0.75);">
        No worries at all — but just know the offer stands.<br>
        Whenever you change your mind, I'll be here. 😊
      </p>
      <div class="divider"></div>
      <p style="font-size:0.85rem; color:rgba(180,140,170,0.5); letter-spacing:0.06em; text-transform:uppercase;">
        (You can always refresh and reconsider 😉)
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Wait… actually yes 🫶", type="primary", use_container_width=True):
            st.session_state.stage = 1
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1 — She Said Yes  (with confetti + falling petals)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == 1:
    # ── Full-screen confetti + petal canvas ──────────────────────────────────
    components.html("""
<!DOCTYPE html>
<html>
<head>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: transparent; overflow: hidden; }
  canvas { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 9999; }
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
const canvas = document.getElementById('c');
const ctx    = canvas.getContext('2d');
canvas.width  = window.innerWidth;
canvas.height = window.innerHeight;

// ── Particle pool ──────────────────────────────────────────────────────────
const COLORS = [
  '#e8a0c8', '#f4d0e8', '#c04080', '#d060a0',
  '#b040a0', '#f8e0f4', '#ff8fbe', '#ff6fa8',
  '#ffd6ec', '#a020a0'
];

const PETALS = ['🌸', '🌹', '🌺', '✨', '💕', '🌷'];

const particles = [];
const TOTAL     = 160;

function rand(a, b) { return a + Math.random() * (b - a); }

class Particle {
  constructor(burst) {
    this.reset(burst);
  }
  reset(burst) {
    // Starting position — burst from center-top or random top edge
    this.x  = burst ? canvas.width / 2 : rand(0, canvas.width);
    this.y  = burst ? rand(-40, 0)      : rand(-80, -10);

    // Velocity
    const angle = burst ? rand(-Math.PI * 1.4, -Math.PI * 0.6) : rand(0.1, 0.4);
    const speed = burst ? rand(4, 14) : rand(1.2, 3.5);
    this.vx = burst ? Math.cos(angle) * speed : rand(-0.8, 0.8);
    this.vy = burst ? Math.sin(angle) * speed : speed;

    this.gravity   = rand(0.08, 0.22);
    this.drag      = rand(0.97, 0.995);
    this.rotation  = rand(0, Math.PI * 2);
    this.rotSpeed  = rand(-0.12, 0.12);
    this.alpha     = 1;
    this.fadeSpeed = rand(0.004, 0.012);
    this.color     = COLORS[Math.floor(rand(0, COLORS.length))];
    this.size      = rand(6, 14);
    this.shape     = Math.random() < 0.25 ? 'petal' : (Math.random() < 0.5 ? 'circle' : 'rect');
    this.emoji     = PETALS[Math.floor(rand(0, PETALS.length))];
    this.wobble    = rand(0, Math.PI * 2);
    this.wobbleSpd = rand(0.05, 0.12);
    this.dead      = false;
  }
  update() {
    this.wobble += this.wobbleSpd;
    this.vx     += Math.sin(this.wobble) * 0.04;
    this.vy     += this.gravity;
    this.vx     *= this.drag;
    this.vy     *= this.drag;
    this.x      += this.vx;
    this.y      += this.vy;
    this.rotation += this.rotSpeed;
    this.alpha  -= this.fadeSpeed;
    if (this.alpha <= 0 || this.y > canvas.height + 60) this.dead = true;
  }
  draw() {
    ctx.save();
    ctx.globalAlpha = Math.max(0, this.alpha);
    ctx.translate(this.x, this.y);
    ctx.rotate(this.rotation);
    if (this.shape === 'circle') {
      ctx.beginPath();
      ctx.arc(0, 0, this.size / 2, 0, Math.PI * 2);
      ctx.fillStyle = this.color;
      ctx.fill();
    } else if (this.shape === 'rect') {
      ctx.fillStyle = this.color;
      ctx.fillRect(-this.size / 2, -this.size / 4, this.size, this.size / 2);
    } else {
      // petal emoji
      ctx.font = `${this.size + 4}px serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(this.emoji, 0, 0);
    }
    ctx.restore();
  }
}

// ── Initial burst ──────────────────────────────────────────────────────────
for (let i = 0; i < TOTAL; i++) {
  particles.push(new Particle(i < 80)); // first 80 burst, rest fall from top
}

// ── Extra wave after 600ms ─────────────────────────────────────────────────
setTimeout(() => {
  for (let i = 0; i < 60; i++) particles.push(new Particle(true));
}, 600);

// ── Animation loop ─────────────────────────────────────────────────────────
function loop() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (let i = particles.length - 1; i >= 0; i--) {
    particles[i].update();
    particles[i].draw();
    if (particles[i].dead) particles.splice(i, 1);
  }
  if (particles.length > 0) requestAnimationFrame(loop);
}
loop();

// Resize handler
window.addEventListener('resize', () => {
  canvas.width  = window.innerWidth;
  canvas.height = window.innerHeight;
});
</script>
</body>
</html>
""", height=0)   # height=0 — canvas is position:fixed so it overlays the whole page

    step_dots(1)

    # Greeting headline — updates live as she types
    name = st.session_state.her_name.strip()
    greeting = f"Yes!! {name} said yes! 🎉" if name else "Yes!! She said yes! 🎉"
    subline  = f"You just made my whole day, {name} 🌸" if name else "You just made my whole day 🌸"

    st.markdown(f"""
    <div class="stage-card">
      <div class="float-icon glow-text">🎉</div>
      <h2 style="font-family:'Cormorant Garamond',serif; font-size:2.4rem; font-weight:300; color:#f4d0e8; margin:1.2rem 0 0.4rem;">
        {greeting}
      </h2>
      <p class="subhead">{subline}</p>
      <div class="divider"></div>
      <p class="body-text">
        This is going to be so much fun. Let's figure out the details together so we can plan<br>
        the <em style="font-family:'Cormorant Garamond',serif; color:#e8a0c8; font-style:italic;">perfect</em> evening for you.
      </p>
      <div class="petal-row">🌹 ✨ 🌹</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Name input ────────────────────────────────────────────────────────────
    st.write("")
    st.markdown("""
    <p style="text-align:center; font-family:'Cormorant Garamond',serif; font-size:1.25rem;
         font-style:italic; color:rgba(230,190,215,0.85); margin-bottom:0.6rem;">
      First, what's your name? ✨
    </p>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name_input = st.text_input(
            "Your name",
            value=st.session_state.her_name,
            placeholder="Enter your name…",
            label_visibility="collapsed",
        )
        if name_input != st.session_state.her_name:
            st.session_state.her_name = name_input
            st.rerun()

        st.write("")
        btn_label = f"Let's plan it, {name_input.strip()} →" if name_input.strip() else "Let's plan it →"
        if st.button(btn_label, type="primary", use_container_width=True, disabled=not name_input.strip()):
            st.session_state.stage = 2
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2 — Pick a Time
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == 2:
    step_dots(2)
    name = st.session_state.her_name.strip()
    time_q = f"What time works best for you, {name}?" if name else "What time works best for you?"
    st.markdown(f"""
    <div class="stage-card">
      <p class="subhead">Step 1 of 3</p>
      <h2 style="font-family:'Cormorant Garamond',serif; font-size:2rem; font-weight:300; color:#f0d8f0; margin-bottom:0.4rem;">
        {time_q}
      </h2>
      <p class="body-text" style="font-size:0.92rem; color:rgba(210,180,205,0.7); margin-bottom:1.5rem;">
        Pick whichever slot fits your vibe.
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    time_slots = [
        ("🌅", "Early Afternoon", "12:00 PM – 2:00 PM"),
        ("☀️", "Late Afternoon",  "3:00 PM – 5:00 PM"),
        ("🌆", "Early Evening",   "6:00 PM – 7:00 PM"),
        ("🌙", "Evening",         "7:00 PM – 9:00 PM"),
        ("✨", "Late Night",      "9:00 PM +"),
    ]

    col1, col2 = st.columns(2)
    for i, (icon, label, hours) in enumerate(time_slots):
        col = col1 if i % 2 == 0 else col2
        is_selected = st.session_state.chosen_time == label
        slot_class = "time-slot-selected" if is_selected else "time-slot"
        with col:
            st.markdown(f'<div class="{slot_class}">', unsafe_allow_html=True)
            if st.button(f"{icon}  {label}\n{hours}", key=f"time_{i}", use_container_width=True):
                st.session_state.chosen_time = label
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.chosen_time:
        st.markdown(f"""
        <div style="text-align:center; padding:0.8rem; background:rgba(180,50,130,0.12);
             border:1px solid rgba(200,90,160,0.3); border-radius:12px; margin:0.5rem 0 1rem;">
          <span style="font-size:0.88rem; color:rgba(230,190,215,0.9);">
            ✓ &nbsp; {st.session_state.chosen_time} selected
          </span>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Next →", type="primary", use_container_width=True):
                st.session_state.stage = 3
                st.rerun()

    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Back", type="secondary", use_container_width=True):
            st.session_state.stage = 1
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3 — Pick a Date
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == 3:
    step_dots(3)
    st.markdown("""
    <div class="stage-card">
      <p class="subhead">Step 2 of 3</p>
      <h2 style="font-family:'Cormorant Garamond',serif; font-size:2rem; font-weight:300; color:#f0d8f0; margin-bottom:0.4rem;">
        What date works for you?
      </h2>
      <p class="body-text" style="font-size:0.92rem; color:rgba(210,180,205,0.7);">
        Pick any date that fits your schedule. I'll make it work. 🗓️
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    min_date = date.today() + timedelta(days=1)
    max_date = date.today() + timedelta(days=90)
    chosen = st.date_input(
        "Choose a date",
        value=st.session_state.chosen_date if st.session_state.chosen_date else min_date,
        min_value=min_date, max_value=max_date, label_visibility="collapsed",
    )
    st.session_state.chosen_date = chosen

    if chosen:
        friendly = chosen.strftime("%A, %B %d, %Y")
        st.markdown(f"""
        <div style="text-align:center; padding:0.8rem; background:rgba(180,50,130,0.12);
             border:1px solid rgba(200,90,160,0.3); border-radius:12px; margin:0.8rem 0 1.2rem;">
          <span style="font-size:0.9rem; color:rgba(230,190,215,0.9);">
            🗓 &nbsp; {friendly} &nbsp; — &nbsp; {st.session_state.chosen_time}
          </span>
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Next →", type="primary", use_container_width=True):
            st.session_state.stage = 4
            st.rerun()
        st.write("")
        if st.button("← Back", type="secondary", use_container_width=True):
            st.session_state.stage = 2
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 4 — Location Preference
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == 4:
    step_dots(4)
    name = st.session_state.her_name.strip()
    loc_q = f"Where's the vibe, {name}?" if name else "Where's the vibe?"
    st.markdown(f"""
    <div class="stage-card">
      <p class="subhead">Step 3 of 4</p>
      <h2 style="font-family:'Cormorant Garamond',serif; font-size:2rem; font-weight:300; color:#f0d8f0; margin-bottom:0.4rem;">
        {loc_q}
      </h2>
      <p class="body-text" style="font-size:0.92rem; color:rgba(210,180,205,0.7);">
        Pick the setting that sounds most exciting to you. 📍
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    locations = [
        ("🏡", "Keep It Local",          "Somewhere close, familiar, and cozy"),
        ("🌆", "Go Downtown",            "City lights, good energy, somewhere lively"),
        ("🌿", "Something Outside",      "A park, rooftop, patio, or open air"),
        ("🗺️", "Explore Somewhere New",  "A new spot neither of us has tried"),
        ("🎲", "Surprise Me",            "I trust you — make it a mystery"),
    ]

    for i, (icon, label, desc) in enumerate(locations):
        is_selected = st.session_state.chosen_location == label
        btn_class   = "loc-btn-selected" if is_selected else "loc-btn"
        st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
        if st.button(f"{icon}  {label}  —  {desc}", key=f"loc_{i}", use_container_width=True):
            st.session_state.chosen_location = label
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.chosen_location:
        st.markdown(f"""
        <div style="text-align:center; padding:0.8rem; background:rgba(180,50,130,0.12);
             border:1px solid rgba(200,90,160,0.3); border-radius:12px; margin:1rem 0;">
          <span style="font-size:0.88rem; color:rgba(230,190,215,0.9);">
            ✓ &nbsp; {st.session_state.chosen_location}
          </span>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Next →", type="primary", use_container_width=True):
                st.session_state.stage = 5
                st.rerun()

    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Back", type="secondary", use_container_width=True):
            st.session_state.stage = 3
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 5 — Choose the Vibe
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == 5:
    step_dots(5)
    st.markdown("""
    <div class="stage-card">
      <p class="subhead">Step 4 of 4</p>
      <h2 style="font-family:'Cormorant Garamond',serif; font-size:2rem; font-weight:300; color:#f0d8f0; margin-bottom:0.4rem;">
        What's your date vibe?
      </h2>
      <p class="body-text" style="font-size:0.92rem; color:rgba(210,180,205,0.7);">
        Pick everything that sounds good — I love options. 😄
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    activities = [
        ("🍽️", "Dinner"), ("🍸", "Drinks"), ("🎬", "Movie"), ("⛳", "Mini Golf"),
        ("🍰", "Dessert"), ("🎳", "Bowling"), ("🌃", "City Walk"), ("🎡", "Amusement"),
        ("🍦", "Ice Cream"), ("🎭", "Comedy Show"),
    ]

    cols = st.columns(2)
    for i, (icon, label) in enumerate(activities):
        col = cols[i % 2]
        is_selected = label in st.session_state.chosen_vibes
        btn_class = "option-btn-selected" if is_selected else "option-btn"
        with col:
            st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
            if st.button(f"{icon}  {label}", key=f"vibe_{i}", use_container_width=True):
                if label in st.session_state.chosen_vibes:
                    st.session_state.chosen_vibes.remove(label)
                else:
                    st.session_state.chosen_vibes.append(label)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.chosen_vibes:
        vibe_str = "  ·  ".join([f"{icon} {label}" for icon, label in activities if label in st.session_state.chosen_vibes])
        st.markdown(f"""
        <div style="text-align:center; padding:0.8rem; background:rgba(180,50,130,0.12);
             border:1px solid rgba(200,90,160,0.3); border-radius:12px; margin:1rem 0;">
          <span style="font-size:0.85rem; color:rgba(230,190,215,0.9);">{vibe_str}</span>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Finish ✨", type="primary", use_container_width=True):
                st.session_state.stage = 6
                st.session_state.email_sent = False
                st.rerun()

    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Back", type="secondary", use_container_width=True):
            st.session_state.stage = 4
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 6 — Final Screen (notes + email notification)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == 6:
    st.markdown("""
    <div style="text-align:center; font-size:2rem; letter-spacing:0.5rem;
         animation: fadeUp 0.5s ease both; margin-bottom:1.5rem;">
      🎊 🌹 💫 🌹 🎊
    </div>
    """, unsafe_allow_html=True)

    friendly_date     = st.session_state.chosen_date.strftime("%A, %B %d, %Y") if st.session_state.chosen_date else "TBD"
    friendly_vibes    = ",  ".join(st.session_state.chosen_vibes) if st.session_state.chosen_vibes else "Surprise me!"
    friendly_location = st.session_state.chosen_location if st.session_state.chosen_location else "—"
    name              = st.session_state.her_name.strip()
    final_headline    = f"{name}, get ready for the<br>best date ever 🥰" if name else "Get ready for the<br>best date ever 🥰"
    notes_prompt      = f"Anything else you want me to know, {name}? 💬" if name else "Anything else you want me to know? 💬"

    # ── Summary card ──
    st.markdown(f"""
    <div class="final-card">
      <p class="final-headline glow-text">{final_headline}</p>
      <p style="font-size:0.85rem; color:rgba(200,160,190,0.6); letter-spacing:0.1em;
           text-transform:uppercase; margin:0.8rem 0 1.8rem;">Here's what we've got planned</p>
      <div class="divider"></div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
      <div class="summary-item">
        <span style="font-size:1.3rem;">👤</span>
        <div>
          <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:rgba(200,155,185,0.6); margin-bottom:2px;">Name</div>
          <div style="color:#f0d8f0;">{name if name else "—"}</div>
        </div>
      </div>
      <div class="summary-item">
        <span style="font-size:1.3rem;">🗓</span>
        <div>
          <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:rgba(200,155,185,0.6); margin-bottom:2px;">Date</div>
          <div style="color:#f0d8f0;">{friendly_date}</div>
        </div>
      </div>
      <div class="summary-item">
        <span style="font-size:1.3rem;">⏰</span>
        <div>
          <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:rgba(200,155,185,0.6); margin-bottom:2px;">Time</div>
          <div style="color:#f0d8f0;">{st.session_state.chosen_time}</div>
        </div>
      </div>
      <div class="summary-item">
        <span style="font-size:1.3rem;">📍</span>
        <div>
          <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:rgba(200,155,185,0.6); margin-bottom:2px;">Location Vibe</div>
          <div style="color:#f0d8f0;">{friendly_location}</div>
        </div>
      </div>
      <div class="summary-item">
        <span style="font-size:1.3rem;">✨</span>
        <div>
          <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:rgba(200,155,185,0.6); margin-bottom:2px;">Vibe</div>
          <div style="color:#f0d8f0;">{friendly_vibes}</div>
        </div>
      </div>
    """, unsafe_allow_html=True)

    st.markdown("""
      <div class="divider" style="margin-top:1.5rem;"></div>
      <p style="font-family:'Cormorant Garamond',serif; font-size:1.15rem; font-style:italic;
           color:rgba(220,175,205,0.75); margin-top:1.2rem; line-height:1.7;">
        I can't wait. It's going to be an unforgettable night. 🌙
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Notes / Comments section ──
    st.write("")
    st.markdown(f"""
    <div style="background:linear-gradient(160deg,rgba(255,255,255,0.03),rgba(140,40,100,0.06));
         border:1px solid rgba(180,80,140,0.2); border-radius:20px; padding:2rem 2rem 1.5rem;
         animation: fadeUp 1s ease both;">
      <p style="font-family:'Cormorant Garamond',serif; font-size:1.5rem; font-weight:300;
           color:#f0d8f0; margin:0 0 0.3rem; text-align:center;">
        {notes_prompt}
      </p>
      <p style="font-size:0.88rem; color:rgba(210,175,200,0.6); text-align:center;
           margin-bottom:1.4rem; letter-spacing:0.04em;">
        Allergies, preferences, things you're excited about — drop it here.
      </p>
    </div>
    """, unsafe_allow_html=True)

    notes = st.text_area(
        "Your notes",
        value=st.session_state.her_notes,
        placeholder="e.g. I'm allergic to shellfish, I love rooftop spots, I've always wanted to try mini golf at night… ✨",
        height=120,
        label_visibility="collapsed",
    )
    st.session_state.her_notes = notes

    # ── Send Results button ──
    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if not st.session_state.email_sent:
            if st.button("Send My Answers 💌", type="primary", use_container_width=True):
                with st.spinner("Sending your details…"):
                    ok, err = send_date_results_email(
                        st.session_state.her_name,
                        friendly_date,
                        st.session_state.chosen_time,
                        friendly_location,
                        friendly_vibes,
                        st.session_state.her_notes,
                    )
                if ok:
                    st.session_state.email_sent = True
                    st.rerun()
                elif err == "secrets_missing":
                    st.markdown("""
                    <div class="email-error">
                      ⚙️ Email not configured yet — see the README to add your Gmail credentials.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="email-error">
                      ❌ Couldn't send: {err}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            sent_msg = f"✅ Sent! He's got your details, {name}. Get ready. 🌹" if name else "✅ Sent! He's got your details. Get ready. 🌹"
            st.markdown(f"""
            <div class="email-success">
              {sent_msg}
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Start Over", type="secondary", use_container_width=True):
            for key in list(defaults.keys()):
                st.session_state[key] = defaults[key]
            st.rerun()
