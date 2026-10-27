import html as html_lib
import smtplib
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st
import streamlit.components.v1 as components

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="A Special Invitation",
    page_icon="💌",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# TRANSLATIONS
# Option values are stored as stable keys (e.g. "evening"), so switching
# language never breaks a selection, and the email to you is always in English.
# ══════════════════════════════════════════════════════════════════════════════
LANGS = {"en": "English", "es": "Español", "fr": "Français"}

TIME_ICONS = {
    "early_aft": ":material/light_mode:",
    "late_aft": ":material/wb_sunny:",
    "early_eve": ":material/wb_twilight:",
    "evening": ":material/nightlight:",
    "late_night": ":material/bedtime:",
}
LOC_ICONS = {
    "local": ":material/home:",
    "downtown": ":material/location_city:",
    "outside": ":material/park:",
    "new": ":material/explore:",
    "surprise": ":material/casino:",
}
VIBE_ICONS = {
    "dinner": ":material/restaurant:",
    "drinks": ":material/local_bar:",
    "movie": ":material/movie:",
    "minigolf": ":material/golf_course:",
    "dessert": ":material/cake:",
    "bowling": ":material/sports_and_outdoors:",
    "walk": ":material/directions_walk:",
    "amusement": ":material/attractions:",
    "icecream": ":material/icecream:",
    "comedy": ":material/theater_comedy:",
}

T = {
    # ───────────────────────────── ENGLISH ─────────────────────────────
    "en": {
        "lang_label": "Language",
        "eyebrow": "A personal invitation",
        "hero_title": "I have a question<br>for <em>you</em>",
        "hero_body": "There's someone I've been thinking about — and that someone is you. "
                     "I'd really love the chance to take you out and show you a genuinely great time.",
        "hero_ask": "Will you go on a date with me?",
        "yes": "Yes, I'd love to",
        "no": "No…",
        "no_title": "Oh… that stings a little.",
        "no_body": "No worries at all — but the offer stands. Whenever you change your mind, I'll be here.",
        "no_hint": "You can always reconsider",
        "no_btn": "Wait… actually yes",
        "yay_title": "You said yes!",
        "yay_title_n": "{name} said yes!",
        "yay_sub": "You just made my whole day.",
        "yay_body": "Let's figure out the details together so I can plan the <em>perfect</em> date for you.",
        "name_q": "First — what's your name?",
        "name_ph": "Your name",
        "plan_btn": "Let's plan it",
        "plan_btn_n": "Let's plan it, {name}",
        "step": "Step {n} of {total}",
        "next": "Continue",
        "back": "Back",
        "time_q": "What time works best?",
        "time_q_n": "What time works best, {name}?",
        "time_sub": "Pick whichever slot fits your vibe.",
        "date_q": "Which day works for you?",
        "date_sub": "Any day in the next three months — I'll make it work.",
        "date_label": "Date",
        "loc_q": "Where's the vibe?",
        "loc_q_n": "Where's the vibe, {name}?",
        "loc_sub": "Pick the setting that sounds most exciting.",
        "vibe_q": "What sounds fun?",
        "vibe_sub": "Choose as many as you like — I love options.",
        "finish": "See our plan",
        "final_title": "Get ready for the best date ever",
        "final_title_n": "{name}, get ready for the best date ever",
        "final_eyebrow": "Here's the plan",
        "lbl_name": "Name", "lbl_date": "Date", "lbl_time": "Time",
        "lbl_loc": "Setting", "lbl_vibe": "Activities",
        "final_close": "I can't wait. It's going to be an unforgettable night.",
        "notes_q": "Anything else I should know?",
        "notes_q_n": "Anything else I should know, {name}?",
        "notes_sub": "Allergies, preferences, things you're excited about.",
        "notes_ph": "e.g. I'm allergic to shellfish, I love rooftop spots…",
        "send": "Send my answers",
        "sending": "Sending…",
        "sent": "Sent! He's got your details. Get ready.",
        "sent_n": "Sent! He's got your details, {name}. Get ready.",
        "err_cfg": "Email isn't configured yet — see the README to add Gmail credentials.",
        "err_send": "Couldn't send: {err}",
        "restart": "Start over",
        "surprise": "Surprise me!",
        "date_fmt": "MM/DD/YYYY",
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "months": ["January", "February", "March", "April", "May", "June", "July",
                   "August", "September", "October", "November", "December"],
        "times": {
            "early_aft": ("Early afternoon", "12 – 2 PM"),
            "late_aft": ("Late afternoon", "3 – 5 PM"),
            "early_eve": ("Early evening", "6 – 7 PM"),
            "evening": ("Evening", "7 – 9 PM"),
            "late_night": ("Late night", "9 PM +"),
        },
        "locs": {
            "local": ("Keep it local", "Somewhere close, familiar and cozy"),
            "downtown": ("Go downtown", "City lights and good energy"),
            "outside": ("Something outside", "A park, rooftop or patio"),
            "new": ("Explore somewhere new", "A spot neither of us has tried"),
            "surprise": ("Surprise me", "I trust you — make it a mystery"),
        },
        "vibes": {
            "dinner": "Dinner", "drinks": "Drinks", "movie": "Movie", "minigolf": "Mini golf",
            "dessert": "Dessert", "bowling": "Bowling", "walk": "City walk",
            "amusement": "Amusement park", "icecream": "Ice cream", "comedy": "Comedy show",
        },
    },
    # ───────────────────────────── ESPAÑOL ─────────────────────────────
    "es": {
        "lang_label": "Idioma",
        "eyebrow": "Una invitación especial",
        "hero_title": "Tengo una pregunta<br>para <em>ti</em>",
        "hero_body": "Hay alguien en quien he estado pensando — y esa persona eres tú. "
                     "Me encantaría invitarte a salir y hacerte pasar un momento increíble.",
        "hero_ask": "¿Quieres salir conmigo?",
        "yes": "Sí, me encantaría",
        "no": "No…",
        "no_title": "Ay… eso duele un poquito.",
        "no_body": "No pasa nada — pero la invitación sigue en pie. Cuando cambies de opinión, aquí estaré.",
        "no_hint": "Siempre puedes reconsiderarlo",
        "no_btn": "Espera… en realidad sí",
        "yay_title": "¡Dijiste que sí!",
        "yay_title_n": "¡{name} dijo que sí!",
        "yay_sub": "Me acabas de alegrar el día.",
        "yay_body": "Organicemos los detalles juntos para planear la cita <em>perfecta</em> para ti.",
        "name_q": "Primero — ¿cómo te llamas?",
        "name_ph": "Tu nombre",
        "plan_btn": "Vamos a planearla",
        "plan_btn_n": "Vamos a planearla, {name}",
        "step": "Paso {n} de {total}",
        "next": "Continuar",
        "back": "Atrás",
        "time_q": "¿Qué horario te queda mejor?",
        "time_q_n": "¿Qué horario te queda mejor, {name}?",
        "time_sub": "Elige el que más vaya contigo.",
        "date_q": "¿Qué día te viene bien?",
        "date_sub": "Cualquier día de los próximos tres meses — yo me adapto.",
        "date_label": "Fecha",
        "loc_q": "¿Qué ambiente prefieres?",
        "loc_q_n": "¿Qué ambiente prefieres, {name}?",
        "loc_sub": "Elige el lugar que más te emocione.",
        "vibe_q": "¿Qué te apetece hacer?",
        "vibe_sub": "Elige todo lo que quieras — me encantan las opciones.",
        "finish": "Ver nuestro plan",
        "final_title": "Prepárate para la mejor cita de tu vida",
        "final_title_n": "{name}, prepárate para la mejor cita de tu vida",
        "final_eyebrow": "Este es el plan",
        "lbl_name": "Nombre", "lbl_date": "Fecha", "lbl_time": "Hora",
        "lbl_loc": "Lugar", "lbl_vibe": "Actividades",
        "final_close": "No puedo esperar. Va a ser una noche inolvidable.",
        "notes_q": "¿Algo más que deba saber?",
        "notes_q_n": "¿Algo más que deba saber, {name}?",
        "notes_sub": "Alergias, preferencias, cosas que te hagan ilusión.",
        "notes_ph": "p. ej. Soy alérgica al marisco, me encantan las terrazas…",
        "send": "Enviar mis respuestas",
        "sending": "Enviando…",
        "sent": "¡Enviado! Ya tiene todos los detalles. Prepárate.",
        "sent_n": "¡Enviado! Ya tiene todos los detalles, {name}. Prepárate.",
        "err_cfg": "El correo aún no está configurado — revisa el README.",
        "err_send": "No se pudo enviar: {err}",
        "restart": "Empezar de nuevo",
        "surprise": "¡Sorpréndeme!",
        "date_fmt": "DD/MM/YYYY",
        "days": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"],
        "months": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                   "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
        "times": {
            "early_aft": ("Primera hora de la tarde", "12:00 – 14:00"),
            "late_aft": ("Media tarde", "15:00 – 17:00"),
            "early_eve": ("Al atardecer", "18:00 – 19:00"),
            "evening": ("Por la noche", "19:00 – 21:00"),
            "late_night": ("Tarde en la noche", "21:00 +"),
        },
        "locs": {
            "local": ("Algo cerca", "Un lugar cercano, conocido y acogedor"),
            "downtown": ("En el centro", "Luces de la ciudad y buen ambiente"),
            "outside": ("Al aire libre", "Un parque, una terraza o un patio"),
            "new": ("Descubrir algo nuevo", "Un sitio que ninguno conoce"),
            "surprise": ("Sorpréndeme", "Confío en ti — que sea un misterio"),
        },
        "vibes": {
            "dinner": "Cena", "drinks": "Copas", "movie": "Cine", "minigolf": "Minigolf",
            "dessert": "Postre", "bowling": "Bolos", "walk": "Paseo por la ciudad",
            "amusement": "Parque de atracciones", "icecream": "Helado", "comedy": "Show de comedia",
        },
    },
    # ───────────────────────────── FRANÇAIS ────────────────────────────
    "fr": {
        "lang_label": "Langue",
        "eyebrow": "Une invitation personnelle",
        "hero_title": "J'ai une question<br>pour <em>toi</em>",
        "hero_body": "Il y a quelqu'un à qui je pense souvent — et cette personne, c'est toi. "
                     "J'adorerais t'inviter à sortir et te faire passer un vrai bon moment.",
        "hero_ask": "Veux-tu sortir avec moi ?",
        "yes": "Oui, avec plaisir",
        "no": "Non…",
        "no_title": "Oh… ça pique un peu.",
        "no_body": "Aucun souci — mais l'invitation tient toujours. Si tu changes d'avis, je serai là.",
        "no_hint": "Tu peux toujours reconsidérer",
        "no_btn": "Attends… en fait, oui",
        "yay_title": "Tu as dit oui !",
        "yay_title_n": "{name} a dit oui !",
        "yay_sub": "Tu viens d'illuminer ma journée.",
        "yay_body": "Organisons les détails ensemble pour que je prépare le rendez-vous <em>parfait</em>.",
        "name_q": "D'abord — comment tu t'appelles ?",
        "name_ph": "Ton prénom",
        "plan_btn": "On s'organise",
        "plan_btn_n": "On s'organise, {name}",
        "step": "Étape {n} sur {total}",
        "next": "Continuer",
        "back": "Retour",
        "time_q": "Quel moment te convient le mieux ?",
        "time_q_n": "Quel moment te convient le mieux, {name} ?",
        "time_sub": "Choisis le créneau qui te ressemble.",
        "date_q": "Quel jour t'arrange ?",
        "date_sub": "N'importe quel jour dans les trois prochains mois — je m'adapte.",
        "date_label": "Date",
        "loc_q": "Quelle ambiance ?",
        "loc_q_n": "Quelle ambiance, {name} ?",
        "loc_sub": "Choisis le cadre qui te fait le plus envie.",
        "vibe_q": "Qu'est-ce qui te tente ?",
        "vibe_sub": "Choisis-en autant que tu veux — j'adore avoir le choix.",
        "finish": "Voir notre programme",
        "final_title": "Prépare-toi pour le meilleur rendez-vous",
        "final_title_n": "{name}, prépare-toi pour le meilleur rendez-vous",
        "final_eyebrow": "Voici le programme",
        "lbl_name": "Prénom", "lbl_date": "Date", "lbl_time": "Heure",
        "lbl_loc": "Cadre", "lbl_vibe": "Activités",
        "final_close": "J'ai hâte. Ça va être une soirée inoubliable.",
        "notes_q": "Autre chose que je devrais savoir ?",
        "notes_q_n": "Autre chose que je devrais savoir, {name} ?",
        "notes_sub": "Allergies, préférences, ce qui te fait envie.",
        "notes_ph": "ex. Je suis allergique aux fruits de mer, j'adore les rooftops…",
        "send": "Envoyer mes réponses",
        "sending": "Envoi…",
        "sent": "Envoyé ! Il a tous les détails. Prépare-toi.",
        "sent_n": "Envoyé ! Il a tous les détails, {name}. Prépare-toi.",
        "err_cfg": "L'e-mail n'est pas encore configuré — voir le README.",
        "err_send": "Échec de l'envoi : {err}",
        "restart": "Recommencer",
        "surprise": "Surprends-moi !",
        "date_fmt": "DD/MM/YYYY",
        "days": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
        "months": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
                   "août", "septembre", "octobre", "novembre", "décembre"],
        "times": {
            "early_aft": ("Début d'après-midi", "12h – 14h"),
            "late_aft": ("Fin d'après-midi", "15h – 17h"),
            "early_eve": ("Début de soirée", "18h – 19h"),
            "evening": ("Soirée", "19h – 21h"),
            "late_night": ("Tard le soir", "21h +"),
        },
        "locs": {
            "local": ("Rester dans le coin", "Un endroit proche, familier et cosy"),
            "downtown": ("En centre-ville", "Les lumières de la ville et de l'ambiance"),
            "outside": ("En plein air", "Un parc, un rooftop ou une terrasse"),
            "new": ("Découvrir un nouvel endroit", "Un lieu qu'aucun de nous ne connaît"),
            "surprise": ("Surprends-moi", "Je te fais confiance — garde le mystère"),
        },
        "vibes": {
            "dinner": "Dîner", "drinks": "Un verre", "movie": "Cinéma", "minigolf": "Mini-golf",
            "dessert": "Dessert", "bowling": "Bowling", "walk": "Balade en ville",
            "amusement": "Parc d'attractions", "icecream": "Glace", "comedy": "Spectacle d'humour",
        },
    },
}

# ── Session State Init ─────────────────────────────────────────────────────
defaults = {
    "stage": 0,
    "her_name": "",
    "chosen_time": None,       # key from TIME_ICONS
    "chosen_date": None,
    "chosen_location": None,   # key from LOC_ICONS
    "chosen_vibes": [],        # keys from VIBE_ICONS
    "her_notes": "",
    "email_sent": False,
    "confetti_done": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v if not isinstance(v, list) else list(v)
if "lang" not in st.session_state:
    st.session_state.lang = "en"


# ── Helpers ────────────────────────────────────────────────────────────────
def L():
    return T[st.session_state.lang]


def esc(s) -> str:
    return html_lib.escape(str(s or ""))


def name() -> str:
    return st.session_state.her_name.strip()


def t(key: str, **kw) -> str:
    """Translated string. If a `<key>_n` variant exists and we know her name, use it."""
    n = name()
    tbl = L()
    if n and f"{key}_n" in tbl:
        return tbl[f"{key}_n"].format(name=esc(n), **kw)
    return tbl[key].format(**kw)


def t_plain(key: str) -> str:
    """Same as t() but unescaped — for widget labels (Streamlit escapes those itself)."""
    n = name()
    tbl = L()
    if n and f"{key}_n" in tbl:
        return tbl[f"{key}_n"].format(name=n)
    return tbl[key]


def fmt_date(d: date, lang: str) -> str:
    tbl = T[lang]
    day, month = tbl["days"][d.weekday()], tbl["months"][d.month - 1]
    if lang == "es":
        return f"{day}, {d.day} de {month} de {d.year}"
    if lang == "fr":
        return f"{day} {d.day} {month} {d.year}"
    return f"{day}, {month} {d.day}, {d.year}"


def go(stage: int):
    st.session_state.stage = stage
    st.rerun()


def progress(step: int, total: int = 4):
    pct = step / total * 100
    st.markdown(
        f"""<div class="progress" role="progressbar" aria-valuenow="{step}" aria-valuemin="0" aria-valuemax="{total}">
              <div class="progress-label">{t("step", n=step, total=total)}</div>
              <div class="progress-track"><div class="progress-fill" style="width:{pct:.0f}%"></div></div>
            </div>""",
        unsafe_allow_html=True,
    )


def heading(title: str, sub: str = "", eyebrow: str = ""):
    eb = f'<p class="eyebrow">{eyebrow}</p>' if eyebrow else ""
    sb = f'<p class="lede">{sub}</p>' if sub else ""
    st.markdown(f'<div class="heading">{eb}<h2 class="title">{title}</h2>{sb}</div>',
                unsafe_allow_html=True)


def nav(back_to: int | None, next_to: int | None, next_label: str | None = None, next_ok: bool = True):
    """Back / Continue row. Continue is disabled (not hidden) until a choice is made."""
    with st.container(key="navrow"):
        c1, c2 = st.columns([1, 2], gap="small")
    with c1:
        if back_to is not None and st.button(t("back"), icon=":material/arrow_back:",
                                             type="tertiary", use_container_width=True, key="nav_back"):
            go(back_to)
    with c2:
        if next_to is not None and st.button(next_label or t("next"), icon=":material/arrow_forward:",
                                             icon_position="right", type="primary",
                                             use_container_width=True, disabled=not next_ok, key="nav_next"):
            go(next_to)


# ── Styles ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Manrope:wght@400;500;600;700&display=swap');

:root {
  --bg: #0b0710;
  --surface: rgba(255,255,255,0.045);
  --surface-hi: rgba(255,255,255,0.075);
  --border: rgba(255,255,255,0.09);
  --border-hi: rgba(244,114,182,0.55);
  --text: #f6eef5;
  --muted: #b9a8b8;          /* 7.9:1 on --bg */
  --accent: #f472b6;
  --accent-2: #a78bfa;
  --gold: #f3d3a4;
  --grad: linear-gradient(135deg, #f472b6 0%, #c084fc 55%, #a78bfa 100%);
  --radius: 22px;
  --ease: cubic-bezier(.2,.8,.2,1);
}

/* ── Canvas ── */
html, body, [data-testid="stAppViewContainer"] { background: var(--bg) !important; }
[data-testid="stAppViewContainer"]::before,
[data-testid="stAppViewContainer"]::after {
  content: ""; position: fixed; z-index: 0; pointer-events: none; border-radius: 50%;
  filter: blur(90px); opacity: .55;
}
[data-testid="stAppViewContainer"]::before {
  width: 520px; height: 520px; top: -180px; left: 50%; transform: translateX(-60%);
  background: radial-gradient(circle, rgba(244,114,182,.55), transparent 65%);
  animation: drift 18s ease-in-out infinite alternate;
}
[data-testid="stAppViewContainer"]::after {
  width: 460px; height: 460px; bottom: -200px; right: -120px;
  background: radial-gradient(circle, rgba(167,139,250,.45), transparent 65%);
  animation: drift 22s ease-in-out infinite alternate-reverse;
}
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebar"],
[data-testid="stDecoration"], footer { display: none !important; }
.block-container { max-width: 600px !important; padding: 2.5rem 1.25rem 4rem !important; position: relative; z-index: 1; }
::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-thumb { background: rgba(244,114,182,.25); border-radius: 3px; }

/* ── Type ── */
html, body, p, div, label, input, textarea, button { font-family: 'Manrope', system-ui, sans-serif; }
.title, .hero-title {
  font-family: 'Instrument Serif', Georgia, serif !important; font-weight: 400 !important;
  color: var(--text) !important; letter-spacing: -0.01em; text-wrap: balance;
}
.hero-title { font-size: clamp(2.6rem, 9vw, 3.8rem) !important; line-height: 1.02 !important; margin: .35rem 0 1.1rem !important; padding: 0 !important; }
.title { font-size: clamp(1.9rem, 6vw, 2.45rem) !important; line-height: 1.1 !important; margin: .25rem 0 .5rem !important; padding: 0 !important; }
.hero-title em, .title em, .lede em {
  font-style: italic; background: var(--grad); -webkit-background-clip: text; background-clip: text; color: transparent;
}
.eyebrow {
  font-size: .72rem; font-weight: 600; letter-spacing: .18em; text-transform: uppercase;
  color: var(--gold); margin: 0 !important;
}
.lede { color: var(--muted); font-size: 1rem; line-height: 1.6; margin: 0 !important; text-wrap: pretty; }
.heading { text-align: center; margin-bottom: 1.4rem; animation: rise .6s var(--ease) both; }
.ask {
  font-family: 'Instrument Serif', Georgia, serif; font-style: italic; font-size: 1.65rem;
  color: var(--text); margin: 1.4rem 0 .2rem !important;
}
.rule { height: 1px; margin: 1.5rem auto; width: 60%; background: linear-gradient(90deg, transparent, rgba(244,114,182,.45), transparent); }

/* ── Cards: any keyed container named card_* ── */
[class*="st-key-card"] {
  background: linear-gradient(160deg, rgba(255,255,255,.06), rgba(255,255,255,.02));
  border: 1px solid var(--border); border-radius: var(--radius);
  padding: 2.2rem 1.6rem 1.6rem; backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 30px 80px -30px rgba(0,0,0,.8), inset 0 1px 0 rgba(255,255,255,.06);
  animation: rise .7s var(--ease) both;
}
@media (max-width: 480px) { [class*="st-key-card"] { padding: 1.8rem 1.1rem 1.2rem; } }

/* ── Monogram badge ── */
.badge {
  width: 64px; height: 64px; margin: 0 auto .9rem; border-radius: 50%;
  display: grid; place-items: center; background: var(--grad);
  box-shadow: 0 10px 40px -8px rgba(244,114,182,.7); animation: float 4s ease-in-out infinite;
}
.badge svg { width: 28px; height: 28px; }

/* ── Language switcher ── */
.st-key-langbar { align-items: center; margin-bottom: 1.2rem; }
.st-key-langbar [data-testid="stButtonGroup"] { display: flex; justify-content: center; }

/* ── Progress ── */
.progress { margin: 0 0 1.4rem; }
.progress-label { font-size: .72rem; letter-spacing: .16em; text-transform: uppercase; color: var(--muted); text-align: center; margin-bottom: .6rem; font-weight: 600; }
.progress-track { height: 4px; border-radius: 4px; background: rgba(255,255,255,.08); overflow: hidden; }
.progress-fill { height: 100%; background: var(--grad); border-radius: 4px; transition: width .5s var(--ease); box-shadow: 0 0 12px rgba(244,114,182,.6); }

/* ── Buttons (base) ── */
.stButton > button {
  min-height: 48px; border-radius: 999px; font-weight: 600; font-size: .95rem; letter-spacing: .01em;
  transition: transform .18s var(--ease), box-shadow .25s var(--ease), background .25s var(--ease), border-color .25s var(--ease) !important;
}
.stButton > button:focus-visible { outline: 2px solid var(--accent) !important; outline-offset: 3px !important; }
.stButton > button[data-testid="stBaseButton-primary"] {
  background: var(--grad) !important; border: none !important; color: #1a0b16 !important;
  box-shadow: 0 10px 30px -10px rgba(244,114,182,.75);
}
.stButton > button[data-testid="stBaseButton-primary"] p { color: #1a0b16 !important; }
.stButton > button[data-testid="stBaseButton-primary"]:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 16px 40px -12px rgba(244,114,182,.9); }
.stButton > button[data-testid="stBaseButton-primary"]:disabled { opacity: .35; box-shadow: none; }
.stButton > button[data-testid="stBaseButton-secondary"] {
  background: transparent !important; border: 1px solid var(--border) !important; color: var(--muted) !important;
}
.stButton > button[data-testid="stBaseButton-secondary"]:hover { border-color: rgba(255,255,255,.25) !important; color: var(--text) !important; }
.stButton > button[data-testid="stBaseButton-tertiary"] { color: var(--muted) !important; }
.stButton > button[data-testid="stBaseButton-tertiary"]:hover { color: var(--text) !important; }
.stButton > button:active:not(:disabled) { transform: scale(.98) !important; }

/* ── Option tiles: keyed containers opt_* (idle) and sel_* (selected) ── */
[class*="st-key-opt_"] .stButton > button,
[class*="st-key-sel_"] .stButton > button {
  min-height: 58px; border-radius: 16px; justify-content: flex-start; text-align: left;
  padding: .85rem 1.1rem; font-weight: 500; font-size: .95rem;
}
[class*="st-key-opt_"] .stButton > button {
  background: var(--surface) !important; border: 1px solid var(--border) !important; color: var(--text) !important;
}
[class*="st-key-opt_"] .stButton > button:hover { background: var(--surface-hi) !important; border-color: rgba(244,114,182,.35) !important; transform: translateY(-1px); }
[class*="st-key-sel_"] .stButton > button {
  background: linear-gradient(135deg, rgba(244,114,182,.22), rgba(167,139,250,.18)) !important;
  border: 1px solid var(--border-hi) !important; color: #fff !important;
  box-shadow: 0 0 0 3px rgba(244,114,182,.12), 0 12px 30px -14px rgba(244,114,182,.8);
}
[class*="st-key-opt_"] .stButton > button > div, [class*="st-key-sel_"] .stButton > button > div { justify-content: flex-start; width: 100%; gap: .6rem; }
[class*="st-key-opt_"] .stButton > button p, [class*="st-key-sel_"] .stButton > button p { text-align: left; }
[class*="st-key-opt_"] [data-testid="stIconMaterial"] { color: var(--muted); }
[class*="st-key-sel_"] [data-testid="stIconMaterial"] { color: var(--accent); }
[class*="st-key-opt_"] strong, [class*="st-key-sel_"] strong { font-weight: 700; }

/* ── Inputs ── */
/* Every layer of every typing field gets the same solid dark fill, so text stays legible
   no matter which Streamlit theme (light/dark/system) is active. */
[data-testid="stTextInput"] [data-baseweb], [data-testid="stDateInput"] [data-baseweb],
[data-testid="stTextArea"] [data-baseweb],
[data-testid="stTextInput"] input, [data-testid="stDateInput"] input, [data-testid="stTextArea"] textarea {
  background-color: #1d1424 !important;
}
[data-testid="stTextInput"] input, [data-testid="stDateInput"] input, [data-testid="stTextArea"] textarea {
  color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; caret-color: var(--accent) !important;
  font-size: 1rem !important; line-height: 1.6 !important; opacity: 1 !important;
}
[data-testid="stTextInput"] input::placeholder, [data-testid="stDateInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
  color: #a898a8 !important; -webkit-text-fill-color: #a898a8 !important; opacity: 1 !important;  /* 6.3:1 on #1d1424 */
}
[data-testid="stTextInput"] > div > div, [data-testid="stDateInput"] > div > div, [data-testid="stTextArea"] > div > div {
  border-radius: 14px !important; border: 1px solid rgba(255,255,255,.18) !important; overflow: hidden;
}
[data-testid="stTextInput"] > div > div:focus-within, [data-testid="stDateInput"] > div > div:focus-within,
[data-testid="stTextArea"] > div > div:focus-within {
  border-color: var(--accent) !important; box-shadow: 0 0 0 3px rgba(244,114,182,.25) !important;
}
[data-testid="stDateInputField"] { background-color: #1d1424 !important; color: #ffffff !important; }
[data-testid="stDateInputField"] * { color: #ffffff !important; }
[data-testid="stTextInput"] [data-baseweb] [data-baseweb], [data-testid="stTextArea"] [data-baseweb] [data-baseweb],
[data-testid="stTextArea"] > div > div > div { border-color: transparent !important; }
[data-testid="InputInstructions"], [data-testid="InputInstructions"] * { color: #b9a8b8 !important; background: transparent !important; }
[data-testid="stTextInput"] input { text-align: center; min-height: 50px; }
[data-testid="stWidgetLabel"] p { color: var(--muted) !important; font-size: .78rem !important; letter-spacing: .12em; text-transform: uppercase; font-weight: 600; }

/* ── Chip summary ── */
.chip {
  display: flex; align-items: center; justify-content: center; gap: .5rem; margin: 1rem 0 0;
  padding: .7rem 1rem; border-radius: 14px; font-size: .9rem; color: var(--text);
  background: rgba(244,114,182,.08); border: 1px solid rgba(244,114,182,.22);
  animation: rise .4s var(--ease) both;
}

/* ── Summary list ── */
.summary { display: grid; gap: .55rem; margin: 1.4rem 0 .4rem; text-align: left; }
.srow {
  display: grid; grid-template-columns: 7.2rem 1fr; gap: .8rem; align-items: baseline;
  padding: .85rem 1rem; border-radius: 14px; background: var(--surface); border: 1px solid var(--border);
}
.srow .k { font-size: .7rem; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); font-weight: 600; }
.srow .v { color: var(--text); font-size: .98rem; }
@media (max-width: 480px) { .srow { grid-template-columns: 1fr; gap: .2rem; } }
@media (max-width: 640px) { .st-key-navrow [data-testid="stHorizontalBlock"] { flex-direction: column-reverse; } }
.closing { font-family: 'Instrument Serif', Georgia, serif; font-style: italic; font-size: 1.25rem; color: var(--muted); text-align: center; margin: 1.2rem 0 0 !important; }

/* ── Status banners ── */
.banner { padding: .9rem 1.1rem; border-radius: 14px; text-align: center; font-size: .92rem; margin: .4rem 0 .8rem; }
.banner.ok  { background: rgba(52,211,153,.10); border: 1px solid rgba(52,211,153,.35); color: #a7f3d0; }
.banner.err { background: rgba(248,113,113,.10); border: 1px solid rgba(248,113,113,.35); color: #fecaca; }

/* ── Motion ── */
@keyframes rise { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
@keyframes drift { from { translate: 0 0; } to { translate: 40px 30px; } }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
</style>
""", unsafe_allow_html=True)

HEART_SVG = ('<svg viewBox="0 0 24 24" fill="#1a0b16" aria-hidden="true"><path d="M12 21s-7.5-4.6-10-9.3C.4 8.4 2.3 4.5 6 4.5c2.2 0 3.6 1.2 4.4 2.4h3.2'
             'C14.4 5.7 15.8 4.5 18 4.5c3.7 0 5.6 3.9 4 7.2C19.5 16.4 12 21 12 21z"/></svg>')


# ── Option tile (selected state via keyed container) ───────────────────────
def option_tile(group: str, key: str, label: str, icon: str, selected: bool) -> bool:
    prefix = "sel" if selected else "opt"
    with st.container(key=f"{prefix}_{group}_{key}"):
        return st.button(label, icon=icon, key=f"btn_{group}_{key}", use_container_width=True)


# ── Email Sender (always English, so you can read it) ──────────────────────
def send_date_results_email(name_str, date_str, time_str, location_str, vibes_str, notes_str, lang_str):
    try:
        cfg = st.secrets["email"]
        sender, password, recipient = cfg["sender_address"], cfg["app_password"], cfg["recipient_address"]

        nm = name_str.strip()
        display_name = nm or "She"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"💌 {nm or 'Her'} said YES — date details inside"
        msg["From"] = sender
        msg["To"] = recipient

        plain = f"""{display_name} said YES! Here are the date details:

Name:      {nm or '(not provided)'}
Date:      {date_str}
Time:      {time_str}
Setting:   {location_str}
Vibe:      {vibes_str}
Language:  {lang_str}
Notes:     {notes_str.strip() or '(none)'}

Go make it the best date ever.
"""
        e = esc
        rows = "".join(
            f'<tr><td style="padding:12px 16px;font:600 11px/1.4 Arial,sans-serif;letter-spacing:.12em;'
            f'text-transform:uppercase;color:#b9a8b8;width:110px;border-bottom:1px solid #2a1f2e">{k}</td>'
            f'<td style="padding:12px 16px;font:15px/1.5 Arial,sans-serif;color:#f6eef5;border-bottom:1px solid #2a1f2e">{e(v)}</td></tr>'
            for k, v in [("Name", nm or "—"), ("Date", date_str), ("Time", time_str),
                         ("Setting", location_str), ("Vibe", vibes_str), ("Language", lang_str)]
        )
        notes_html = "" if not notes_str.strip() else (
            '<div style="margin:20px 16px 0;padding:16px 18px;border-radius:12px;background:#1f1424;border:1px solid #4a2a44">'
            '<div style="font:600 11px Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:#f3d3a4;margin-bottom:6px">Her notes</div>'
            f'<div style="font:italic 15px/1.7 Georgia,serif;color:#f6eef5">{e(notes_str).replace(chr(10), "<br>")}</div></div>'
        )
        html_body = f"""<!DOCTYPE html><html><body style="margin:0;padding:24px;background:#0b0710">
<div style="max-width:560px;margin:0 auto;background:#140d19;border:1px solid #2a1f2e;border-radius:20px;overflow:hidden">
  <div style="padding:36px 28px 26px;text-align:center;background:linear-gradient(135deg,#3a1630,#22163a)">
    <div style="font:600 11px Arial,sans-serif;letter-spacing:.18em;text-transform:uppercase;color:#f3d3a4">It's a date</div>
    <h1 style="margin:10px 0 0;font:italic 400 30px/1.2 Georgia,serif;color:#f6eef5">{e(display_name)} said yes</h1>
  </div>
  <table role="presentation" style="width:100%;border-collapse:collapse;margin-top:8px">{rows}</table>
  {notes_html}
  <p style="text-align:center;padding:24px;margin:0;font:italic 14px Georgia,serif;color:#b9a8b8">Now go make it the best date ever.</p>
</div></body></html>"""

        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        return True, None
    except (KeyError, FileNotFoundError):  # no [email] block / no secrets.toml at all
        return False, "secrets_missing"
    except Exception as ex:
        return False, str(ex)


# ── Confetti (injected into the parent page so it overlays the whole app) ──
CONFETTI_JS = """
<script>
(function () {
  const doc = (function(){ try { return window.parent.document; } catch(e) { return document; } })();
  const win = doc.defaultView || window;
  if (win.matchMedia && win.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const old = doc.getElementById('date-confetti'); if (old) old.remove();
  const c = doc.createElement('canvas'); c.id = 'date-confetti';
  Object.assign(c.style, {position:'fixed', inset:'0', width:'100vw', height:'100vh', pointerEvents:'none', zIndex: 9999});
  doc.body.appendChild(c);
  const ctx = c.getContext('2d'); const dpr = win.devicePixelRatio || 1;
  function size(){ c.width = win.innerWidth * dpr; c.height = win.innerHeight * dpr; ctx.setTransform(dpr,0,0,dpr,0,0); }
  size(); win.addEventListener('resize', size);
  const W = () => win.innerWidth, H = () => win.innerHeight;
  const COLORS = ['#f472b6','#f9a8d4','#c084fc','#a78bfa','#f3d3a4','#ffffff'];
  const r = (a,b) => a + Math.random()*(b-a);
  const P = [];
  function spawn(n, burst){
    for (let i=0;i<n;i++){
      const a = burst ? r(-Math.PI*0.85, -Math.PI*0.15) : r(0.3, 0.6)*Math.PI;
      const s = burst ? r(6, 15) : r(1, 3);
      P.push({x: burst ? W()/2 + r(-40,40) : r(0,W()), y: burst ? H()*0.42 : r(-60,-10),
        vx: Math.cos(a)*s, vy: Math.sin(a)*s, g: r(.12,.25), rot: r(0,6.28), vr: r(-.2,.2),
        w: r(6,11), h: r(3,6), c: COLORS[(Math.random()*COLORS.length)|0],
        heart: Math.random() < .22, life: 1, decay: r(.004,.009)});
    }
  }
  function heart(x,y,s){ ctx.beginPath(); ctx.moveTo(0,s*.3);
    ctx.bezierCurveTo(-s, -s*.4, -s*.5, -s*1.1, 0, -s*.45);
    ctx.bezierCurveTo(s*.5, -s*1.1, s, -s*.4, 0, s*.3); ctx.fill(); }
  spawn(140, true); setTimeout(() => spawn(70, false), 500);
  (function loop(){
    ctx.clearRect(0,0,W(),H());
    for (let i=P.length-1;i>=0;i--){
      const p = P[i]; p.vy += p.g; p.vx *= .985; p.vy *= .985; p.x += p.vx; p.y += p.vy; p.rot += p.vr; p.life -= p.decay;
      if (p.life <= 0 || p.y > H()+40){ P.splice(i,1); continue; }
      ctx.save(); ctx.globalAlpha = Math.max(0,p.life); ctx.translate(p.x,p.y); ctx.rotate(p.rot); ctx.fillStyle = p.c;
      if (p.heart) heart(0,0,p.w*.9); else ctx.fillRect(-p.w/2,-p.h/2,p.w,p.h);
      ctx.restore();
    }
    if (P.length) win.requestAnimationFrame(loop); else c.remove();
  })();
})();
</script>
"""

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 0 — Language + Invitation
# ══════════════════════════════════════════════════════════════════════════════
stage = st.session_state.stage

if stage == 0:
    def _on_lang():
        v = st.session_state.lang_picker
        if v is None:  # clicking the active segment would deselect it; keep current
            st.session_state.lang_picker = st.session_state.lang
        else:
            st.session_state.lang = v

    with st.container(key="langbar"):
        st.segmented_control(
            L()["lang_label"], options=list(LANGS), format_func=lambda k: LANGS[k],
            default=st.session_state.lang, key="lang_picker", on_change=_on_lang,
            label_visibility="collapsed",
        )

    with st.container(key="card_hero"):
        st.markdown(f"""
        <div style="text-align:center">
          <div class="badge">{HEART_SVG}</div>
          <p class="eyebrow">{t("eyebrow")}</p>
          <h1 class="hero-title">{t("hero_title")}</h1>
          <p class="lede">{t("hero_body")}</p>
          <div class="rule"></div>
          <p class="ask">{t("hero_ask")}</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        c1, c2 = st.columns([2, 1], gap="small")
        with c1:
            if st.button(t("yes"), icon=":material/favorite:", type="primary", use_container_width=True, key="yes"):
                go(1)
        with c2:
            if st.button(t("no"), type="secondary", use_container_width=True, key="no"):
                go(-1)


# ══════════════════════════════════════════════════════════════════════════════
# STAGE -1 — Said No
# ══════════════════════════════════════════════════════════════════════════════
elif stage == -1:
    with st.container(key="card_no"):
        st.markdown(f"""
        <div style="text-align:center">
          <p class="eyebrow">{t("no_hint")}</p>
          <h2 class="title">{t("no_title")}</h2>
          <p class="lede">{t("no_body")}</p>
          <div class="rule"></div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(t("no_btn"), icon=":material/favorite:", type="primary", use_container_width=True):
            go(1)


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1 — She Said Yes (confetti + name)
# ══════════════════════════════════════════════════════════════════════════════
elif stage == 1:
    if not st.session_state.confetti_done:
        components.html(CONFETTI_JS, height=0)
        st.session_state.confetti_done = True

    with st.container(key="card_yay"):
        st.markdown(f"""
        <div style="text-align:center">
          <div class="badge">{HEART_SVG}</div>
          <p class="eyebrow">{t("yay_sub")}</p>
          <h2 class="title">{t("yay_title")}</h2>
          <p class="lede">{t("yay_body")}</p>
          <div class="rule"></div>
        </div>
        """, unsafe_allow_html=True)

        st.session_state.her_name = st.text_input(
            t("name_q"), value=st.session_state.her_name, placeholder=L()["name_ph"], max_chars=40,
        )
        st.write("")
        if st.button(t_plain("plan_btn"), icon=":material/arrow_forward:", icon_position="right",
                     type="primary", use_container_width=True, key="plan_btn"):
            if name():
                go(2)
            st.markdown(f'<div class="banner err" role="alert">{t("name_q")}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2 — Time
# ══════════════════════════════════════════════════════════════════════════════
elif stage == 2:
    progress(1)
    heading(t("time_q"), t("time_sub"))
    for k, icon in TIME_ICONS.items():
        label, hours = L()["times"][k]
        if option_tile("time", k, f"**{label}** · {hours}", icon, st.session_state.chosen_time == k):
            st.session_state.chosen_time = k
            st.rerun()
    st.write("")
    nav(1, 3, next_ok=bool(st.session_state.chosen_time))


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3 — Date
# ══════════════════════════════════════════════════════════════════════════════
elif stage == 3:
    progress(2)
    heading(t("date_q"), t("date_sub"))
    min_date = date.today() + timedelta(days=1)
    max_date = date.today() + timedelta(days=90)
    with st.container(key="card_date"):
        chosen = st.date_input(
            L()["date_label"],
            value=st.session_state.chosen_date or min_date,
            min_value=min_date, max_value=max_date, format=L()["date_fmt"],
        )
        st.session_state.chosen_date = chosen
        if chosen and st.session_state.chosen_time:
            tlabel = L()["times"][st.session_state.chosen_time][0]
            st.markdown(f'<div class="chip">{esc(fmt_date(chosen, st.session_state.lang))} · {esc(tlabel)}</div>',
                        unsafe_allow_html=True)
    st.write("")
    nav(2, 4, next_ok=bool(chosen))


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 4 — Location
# ══════════════════════════════════════════════════════════════════════════════
elif stage == 4:
    progress(3)
    heading(t("loc_q"), t("loc_sub"))
    for k, icon in LOC_ICONS.items():
        label, desc = L()["locs"][k]
        if option_tile("loc", k, f"**{label}** — {desc}", icon, st.session_state.chosen_location == k):
            st.session_state.chosen_location = k
            st.rerun()
    st.write("")
    nav(3, 5, next_ok=bool(st.session_state.chosen_location))


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 5 — Activities (multi-select)
# ══════════════════════════════════════════════════════════════════════════════
elif stage == 5:
    progress(4)
    heading(t("vibe_q"), t("vibe_sub"))
    keys = list(VIBE_ICONS)
    cols = st.columns(2, gap="small")
    for i, k in enumerate(keys):
        with cols[i % 2]:
            if option_tile("vibe", k, L()["vibes"][k], VIBE_ICONS[k], k in st.session_state.chosen_vibes):
                if k in st.session_state.chosen_vibes:
                    st.session_state.chosen_vibes.remove(k)
                else:
                    st.session_state.chosen_vibes.append(k)
                st.rerun()
    st.write("")
    st.session_state.email_sent = False
    nav(4, 6, next_label=t("finish"), next_ok=bool(st.session_state.chosen_vibes))


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 6 — Summary + notes + send
# ══════════════════════════════════════════════════════════════════════════════
elif stage == 6:
    lang = st.session_state.lang
    tbl = L()
    d = st.session_state.chosen_date
    time_k, loc_k, vibe_ks = st.session_state.chosen_time, st.session_state.chosen_location, st.session_state.chosen_vibes

    # Localised (for her)
    loc_date = fmt_date(d, lang) if d else "—"
    loc_time = " · ".join(tbl["times"][time_k]) if time_k else "—"
    loc_loc = tbl["locs"][loc_k][0] if loc_k else "—"
    loc_vibes = ", ".join(tbl["vibes"][v] for v in vibe_ks) if vibe_ks else tbl["surprise"]

    with st.container(key="card_final"):
        rows = "".join(
            f'<div class="srow"><span class="k">{tbl[k]}</span><span class="v">{esc(v)}</span></div>'
            for k, v in [("lbl_name", name() or "—"), ("lbl_date", loc_date), ("lbl_time", loc_time),
                         ("lbl_loc", loc_loc), ("lbl_vibe", loc_vibes)]
        )
        st.markdown(f"""
        <div style="text-align:center">
          <div class="badge">{HEART_SVG}</div>
          <p class="eyebrow">{t("final_eyebrow")}</p>
          <h2 class="title">{t("final_title")}</h2>
        </div>
        <div class="summary">{rows}</div>
        <p class="closing">{t("final_close")}</p>
        """, unsafe_allow_html=True)

    st.write("")
    with st.container(key="card_notes"):
        heading(t("notes_q"), t("notes_sub"))
        st.session_state.her_notes = st.text_area(
            t_plain("notes_q"), value=st.session_state.her_notes, placeholder=tbl["notes_ph"],
            height=120, max_chars=1000, label_visibility="collapsed",
        )

        if not st.session_state.email_sent:
            if st.button(t("send"), icon=":material/send:", type="primary", use_container_width=True, key="send"):
                # English values for the email to you
                en = T["en"]
                with st.spinner(tbl["sending"]):
                    ok, err = send_date_results_email(
                        st.session_state.her_name,
                        fmt_date(d, "en") if d else "TBD",
                        " · ".join(en["times"][time_k]) if time_k else "—",
                        en["locs"][loc_k][0] if loc_k else "—",
                        ", ".join(en["vibes"][v] for v in vibe_ks) if vibe_ks else "Surprise me!",
                        st.session_state.her_notes,
                        LANGS[lang],
                    )
                if ok:
                    st.session_state.email_sent = True
                    st.rerun()
                msg = tbl["err_cfg"] if err == "secrets_missing" else tbl["err_send"].format(err=esc(err))
                st.markdown(f'<div class="banner err" role="alert">{msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="banner ok" role="status">{t("sent")}</div>', unsafe_allow_html=True)

    st.write("")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button(tbl["restart"], icon=":material/replay:", type="tertiary", use_container_width=True, key="restart"):
            for k, v in defaults.items():
                st.session_state[k] = v if not isinstance(v, list) else list(v)
            st.rerun()
