# CodingScripts

A personal collection of coding projects spanning web apps, machine learning, games, and automation — built while learning and experimenting across languages and frameworks.

![GitHub last commit](https://img.shields.io/github/last-commit/Leka0207/CodingScripts)
![GitHub repo size](https://img.shields.io/github/repo-size/Leka0207/CodingScripts)
![GitHub stars](https://img.shields.io/github/stars/Leka0207/CodingScripts?style=social)

**Live site:** [leka0207.github.io/CodingScripts](https://leka0207.github.io/CodingScripts/)

---

## Table of Contents

- [About](#about)
- [Project Directory](#project-directory)
- [Getting Started](#getting-started)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Contact](#contact)

---

## About

This repo is a running archive of standalone projects — some built to learn a new library or language feature, others built for fun or for a specific real-world use case. Each folder is self-contained with its own dependencies, so you can drop into any single project without needing the whole repo set up.

---

## Project Directory

### 🌐 Web Apps

| Project | Description |
|---|---|
| **[DateWebsite](./DateWebsite)** | A playful, multi-stage Streamlit app for asking someone on a date — animated invitation flow (ask → pick a time → pick a date → pick the vibe → summary), with results emailed to the organizer via Gmail SMTP on submission. |
| **[Calculator Webpage](./Calculator%20Webpage)** | A browser-based calculator built with HTML, CSS, and JavaScript. |
| **[Website Project](./Website%20Project)** | General front-end web project. |
| **[WeatherApp](./WeatherApp)** | Fetches and displays live weather data for a given location. |

### 🤖 AI & Automation

| Project | Description |
|---|---|
| **[JARVIS](./JARVIS)** | A Jarvis-style AI voice assistant in Python, combining the Anthropic Claude API for language understanding with `speech_recognition` for voice input and `pyttsx3` for spoken responses. Roadmap includes ElevenLabs voice synthesis, Whisper transcription, and expanded tool-use. |
| **[Excel Macro](./Excel%20Macro)** | A VBA macro for automating repetitive tasks in Excel. |

### 📊 Machine Learning & Data

| Project | Description |
|---|---|
| **[CreditCardFraudML](./CreditCardFraudML)** | A machine learning model trained to flag fraudulent credit card transactions. |
| **[OlympicMedalPredictor_ML](./OlympicMedalPredictor_ML)** | Predicts Olympic medal outcomes using historical data and ML models. |
| **[StockPredictorML](./StockPredictorML)** | A machine learning approach to forecasting stock price movement. |
| **[Stock Predictor Web App](./Stock%20Predictor%20Web%20App)** | A web front end for exploring stock predictions interactively. |
| **[S&P500_app](./S%26P500_app)** | An app for tracking or analyzing S&P 500 data. |

### 🎮 Games

| Project | Description |
|---|---|
| **[ChessGame](./ChessGame)** | A playable implementation of chess. |
| **[checkersgame](./checkersgame)** | A playable implementation of checkers. |

### 🧠 Practice & Fundamentals

| Project | Description |
|---|---|
| **[C++](./C%2B%2B)** | C++ programs and exercises covering core language concepts. |
| **[python](./python)** | Python scripts and exercises. |
| **[KDL](./KDL)** | Exploratory project — see the folder for details. |

> Have a look through each folder's own files for setup notes and specifics — this table is a map, not the full documentation.

---

## Getting Started

Clone the repo:

```bash
git clone https://github.com/Leka0207/CodingScripts.git
cd CodingScripts
```

Most Python-based projects follow the same pattern. From inside the project folder:

```bash
pip install -r requirements.txt
```

**Streamlit apps** (like `DateWebsite`, `Stock Predictor Web App`) run with:

```bash
streamlit run app.py
```

**Note:** The `DateWebsite` app sends results by email via Gmail SMTP. To run it yourself, create a `.streamlit/secrets.toml` with your own credentials (see `secrets.toml` in this repo as a reference for the expected structure):

```toml
[email]
sender_address = "your_email@gmail.com"
app_password = "your_16_char_gmail_app_password"
recipient_address = "where_you_want_results@gmail.com"
```

Never commit real credentials to a public repo — use a Gmail [App Password](https://myaccount.google.com/apppasswords), and keep your actual `secrets.toml` out of version control via `.gitignore`.

---

## Tech Stack

- **Languages:** Python, C++, JavaScript, HTML/CSS, VBA
- **Frameworks/Libraries:** Streamlit, pandas, scikit-learn (ML projects), `speech_recognition`, `pyttsx3`
- **APIs:** Anthropic Claude API, Gmail SMTP
- **Deployment:** Streamlit Community Cloud, GitHub Pages

---

## Repository Structure

```
CodingScripts/
├── app.py                    # DateWebsite Streamlit app (root-level entry point)
├── requirements.txt
├── C++/
├── Calculator Webpage/
├── ChessGame/
├── CreditCardFraudML/
├── DateWebsite/
├── Excel Macro/
├── JARVIS/
├── KDL/
├── OlympicMedalPredictor_ML/
├── S&P500_app/
├── Stock Predictor Web App/
├── StockPredictorML/
├── WeatherApp/
├── Website Project/
├── checkersgame/
└── python/
```

---

## Contact

Maintained by [@Leka0207](https://github.com/Leka0207). Feel free to open an issue or pull request if you spot something worth improving.
