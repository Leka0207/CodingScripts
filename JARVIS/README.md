# J.A.R.V.I.S.

A voice assistant that lives on your desktop. It listens for "Hey Jarvis," answers
out loud in a British voice, and puts anything worth reading on a full-screen
heads-up display.

It genuinely controls the machine — volume, apps, media, timers, clipboard — it
can see your screen when you ask about it, it searches the web, and it remembers
things about you between sessions.

---

## Setup

Four steps, about five minutes.

**1. Install Python 3.10 or newer**, then from this folder:

```bash
pip install -r requirements.txt
```

**2. Add your API key.** Copy `.env.example` to `.env` and paste in a key from
[console.anthropic.com](https://console.anthropic.com):

```
ANTHROPIC_API_KEY=sk-ant-...
```

**3. Check everything landed:**

```bash
python run.py doctor
```

**4. Start it:**

```bash
python run.py
```

The HUD opens at `http://127.0.0.1:8123`. Press **F** for fullscreen and drag the
window to whichever monitor you want it to live on.

The first launch downloads the speech models (a few hundred MB). Give it a
minute. After that, startup takes a couple of seconds.

---

## Talking to it

Say **"Hey Jarvis"**, wait for the ring to turn cyan, then speak. After it
replies you have twelve seconds to talk again without the wake word, so
follow-ups feel like a conversation.

| | |
|---|---|
| **Space** | push to talk, if the wake word misses |
| **Esc** | cut it off mid-sentence |
| **/** | jump to the text box |
| **F** | fullscreen |

Things worth trying:

- *"How's the machine holding up?"* — real readings, not guesses
- *"What's on my screen?"* — takes a screenshot and reads it
- *"What's this error mean?"* — same, while you're staring at a stack trace
- *"Remember that I run emissions tests on the GC analyzer"* — stored for good
- *"Set a timer for twenty minutes"* — announces itself out loud
- *"Run the workshop protocol"* — fires a whole routine
- *"What happened with the Fed today?"* — searches the web, puts sources on screen

The rhythm to notice: **it says one line and puts the detail on the HUD.** That's
deliberate. Listening to an AI read a list aloud is miserable, so it doesn't.

---

## Making it yours

Everything configurable is in `config.yaml`.

### Personality

`brain.persona` is the whole character. Rewrite it and Jarvis becomes someone
else entirely — terser, warmer, funnier, whatever you want.

### Protocols

Named routines it runs in one command. The four shipped ones are examples:

```yaml
protocols:
  gaming:
    description: "Rig ready for a session."
    say: "Spinning up. Have fun."
    steps:
      - launch: steam
      - launch: discord
      - volume: 60
```

Steps can be `launch`, `volume`, `timer`, or `ask`. That last one is the
interesting one — it hands an instruction back to Claude with all its tools
available, so a protocol can do real work:

```yaml
      - ask: "Check system status and search for today's news about the Detroit
              auto industry. Put headlines on the HUD, summarise in two sentences."
```

### Apps

The `apps:` block maps nicknames to what actually launches. "Open my editor"
works once you add `editor: "code"`.

### Voice

`tts.voice` accepts any Microsoft Edge voice. `en-GB-RyanNeural` is the default;
`en-GB-ThomasNeural` is drier, `en-GB-SoniaNeural` is female. Free, no key.

For something closer to Paul Bettany, set `tts.engine: elevenlabs`, add
`ELEVENLABS_API_KEY` to `.env`, and put a voice ID in `tts.elevenlabs_voice_id`.

### Model

`brain.model` defaults to `claude-sonnet-5`. Use `claude-opus-5` if you want more
depth and don't mind waiting, or `claude-haiku-4-5` if you want it instant.
`brain.effort: low` keeps replies snappy — raise it to `medium` for harder
questions.

---

## Troubleshooting

**It doesn't hear me.** Run `python run.py devices`, find your microphone's
number, and set `voice.input_device` in the config. If it triggers on random
speech, raise `voice.wake_threshold` to 0.6; if it never triggers, drop it to 0.4.

**It cuts me off mid-sentence.** Raise `voice.silence_ms` to 1200.

**Transcription is sloppy.** Move `voice.stt_model` up to `small.en`. If you have
an NVIDIA card, set `stt_device: cuda` and `stt_compute: float16` — much faster
and more accurate.

**No sound.** Click once anywhere on the HUD. Browsers block audio until the page
has been interacted with.

**It's slow to respond.** Use `claude-haiku-4-5`, keep `effort: low`, and drop the
speech model to `tiny.en`.

---

## How it's built

```
run.py            launcher — run / devices / doctor
config.yaml       everything you'd want to change
core/
  audio.py        mic → wake word → endpointing → Whisper → text
  brain.py        streaming Claude call wrapped in a tool loop
  tools.py        the ten things it can actually do
  server.py       FastAPI + websocket bus
web/              the HUD (one canvas, no framework, no build step)
data/memory.db    what it remembers — plain SQLite, open it any time
```

Speech recognition runs entirely on your machine; audio never leaves it. Only
your transcribed text goes to the API. Speech comes back as MP3 over the
websocket and plays in the browser, which is why you didn't have to install
ffmpeg or any codec.

The ring around the core isn't decoration — it's a rolling six-second history of
real amplitude. Room noise while idle, your voice while listening, the spoken
waveform while it replies. Newest sample at twelve o'clock, sweeping clockwise
into the past.

## A note on shell access

`safety.allow_shell` is off. Turning it on gives Claude a `run_command` tool with
your user's full permissions on your machine. It's genuinely useful and it is a
real risk — a web page it reads could try to talk it into something. Leave it off
unless you have a specific reason.
