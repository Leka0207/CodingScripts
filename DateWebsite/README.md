# 💌 Date Request App

A beautiful multi-stage date invitation app built with Streamlit.
When she finishes, her answers get emailed directly to you.

---

## Flow

1. **Invitation** — Yes / No (with a playful "wait… actually yes" screen if she hits No)
2. **She Said Yes** — Celebration screen
3. **Pick a Time** — 5 time slot options
4. **Pick a Date** — Calendar picker
5. **Choose the Vibe** — Multi-select activity preferences
6. **Final Screen** — Summary card + notes/comments box + "Send My Answers" button → emails you

---

## Email Setup (Gmail App Password)

The app emails you her results via Gmail SMTP. You need a **Gmail App Password** — NOT your regular Gmail password.

### How to get a Gmail App Password

1. Go to your Google Account → **Security**
2. Make sure **2-Step Verification is ON**
3. Search for **"App Passwords"** (or go to myaccount.google.com/apppasswords)
4. Click **Create** → name it "Date App" → copy the 16-character password

### Local development

Create `.streamlit/secrets.toml` (already in `.gitignore` so it won't be committed):

```toml
[email]
sender_address    = "yourgmail@gmail.com"
app_password      = "xxxx xxxx xxxx xxxx"   # 16-char App Password
recipient_address = "youremail@gmail.com"   # where YOU want to receive results
```

---

## Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Deploy to Streamlit Community Cloud (Free)

1. Push this repo to GitHub (**do not push** `.streamlit/secrets.toml` — it's gitignored)
2. Go to [share.streamlit.io](https://share.streamlit.io) → sign in with GitHub
3. **New app** → select your repo → branch `main` → main file `app.py` → **Deploy**
4. Once deployed: App dashboard → **⋮ menu → Settings → Secrets**
5. Paste this and fill in your values:

```toml
[email]
sender_address    = "yourgmail@gmail.com"
app_password      = "xxxx xxxx xxxx xxxx"
recipient_address = "youremail@gmail.com"
```

6. Hit **Save** — the app restarts and email is live
7. Copy the public URL and send it to her 🌹

---

## Files

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit app |
| `requirements.txt` | Python dependencies |
| `.streamlit/secrets.toml` | Your credentials (local only, gitignored) |
| `.gitignore` | Keeps secrets out of GitHub |
