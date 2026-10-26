# 💌 Date Request App

A beautiful multi-stage date invitation app built with Streamlit.
When she finishes, her answers get emailed directly to you.

---

## Flow

1. **Invitation** — Language picker (English / Español / Français) + Yes / No (with a playful "wait… actually yes" screen if she hits No)
2. **She Said Yes** — Confetti + name entry
3. **Pick a Time** — 5 time slots (step 1 of 4)
4. **Pick a Date** — Calendar picker, localized date format (step 2 of 4)
5. **Pick a Setting** — 5 location vibes (step 3 of 4)
6. **Choose Activities** — Multi-select (step 4 of 4)
7. **Final Screen** — Summary card + notes box + "Send my answers" → emails you

The whole flow is shown in her chosen language. **The email you receive is always in English** and includes which language she picked.

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
| `.streamlit/config.toml` | Dark theme + accent colors (commit this one) |
| `.streamlit/secrets.toml` | Your credentials (local only, gitignored) |
| `.gitignore` | Keeps secrets out of GitHub |
