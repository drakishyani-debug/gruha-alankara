# Gruha Alankara 🏠✨
### Interior Design Platform with AR and AI Integration

Gruha Alankara is a locally-hosted Flask web app that lets a user upload
(or capture) a photo of a room, get an AI-style analysis and design
recommendation, preview furniture in AR / 3D, plan a budget, and
"book" furniture through a multilingual (English / Hindi / Telugu)
voice assistant called **buddy** — all with zero cloud dependencies.

---

## 1. Project Structure

```
gruha-alankara/
├── app.py                    # Flask entry point & all routes
├── config.py                 # App configuration
├── models.py                 # SQLite data-access layer (User, Design, Furniture, Booking)
├── requirements.txt
├── .env.example
├── database/
│   ├── db.py                  # Connection helper + init_db()
│   ├── schema.sql              # Table definitions
│   └── designs.db              # Created automatically on first run
├── agents/
│   └── interior_agent.py       # "buddy" — orchestrates the tools + handles chat/booking
├── tools/
│   ├── room_analyzer.py        # Image analysis (dimensions, lighting, palette, edges)
│   ├── style_suggester.py      # Style/palette/material recommendations
│   ├── furniture_optimizer.py  # Furniture list + layout tips + space utilization
│   ├── budget_planner.py       # Budget allocation + price ranges + savings tips
│   └── design_catalog.py       # Saves/lists designs to the catalog
├── static/
│   ├── css/style.css           # Dark theme
│   ├── js/main.js              # Analyze & Design Studio page logic
│   ├── js/voice.js             # buddy voice/chat widget (Web Speech API)
│   ├── js/ar_viewer.js         # Live AR camera overlay + three.js room viewer
│   └── uploads/                # Uploaded room photos
└── templates/
    ├── base.html, index.html, register.html, login.html,
    ├── analyze.html, design.html, catalog.html,
    └── ar_viewer.html, live_ar_camera.html
```

## 2. Prerequisites

- Python 3.8+ (developed/tested on 3.12)
- A modern browser (Chrome/Edge recommended for camera + Web Speech API support)
- No external database, API keys, or cloud account needed

## 3. Setup

```bash
# 1. Clone / unzip the project, then enter the folder
cd gruha-alankara

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app (this also auto-creates database/designs.db on first run)
python app.py
```

Then open **http://127.0.0.1:5000** in your browser. To test camera/AR
features from a phone on the same Wi-Fi network, visit
`http://<your-computer-local-ip>:5000` instead (the dev server binds to
`0.0.0.0`). Note: most browsers require HTTPS for camera access on a
non-localhost address — use `localhost`/`127.0.0.1` for the simplest
testing experience, or set up a local HTTPS tunnel (e.g. `ngrok`) for
mobile testing.

## 4. How to Use

1. **Sign up / Log in.**
2. **Analyze Room** — upload a photo or capture one with your camera;
   the AI tool extracts estimated dimensions, lighting quality, a color
   palette, and a room-complexity score.
3. Click **Proceed to Design** to carry that photo/analysis into the
   **Design Studio**.
4. Pick a **style theme**, **budget**, and **room type**, then click
   **Generate Design**. This runs the full agent pipeline: style
   suggestion → furniture optimization → budget planning.
5. Explore the **Overview / Furniture / Budget / 3D View** tabs.
6. Click **Save to Catalog** to persist the design, then use the
   **buddy** widget (bottom-right) to book furniture by typing or
   speaking, e.g. *"book the sofa"*, *"सोफ़ा बुक करें"*, or
   *"సోఫా బుక్ చేయండి"* — switch the language dropdown first.
7. Visit **My Catalog** to view, duplicate, or delete saved designs, or
   **Live AR Camera** to place furniture silhouettes over your live
   camera feed.

## 5. Important Assumptions & Deviations from the Original Spec

The source project brief referenced several cloud/GPU-dependent
components (IBM Granite models via Hugging Face Transformers, LangChain
+ an LLM endpoint, PostgreSQL, Google Text-to-Speech, Redis). This
build runs **entirely offline/locally** as the brief's own
prerequisites and conclusion emphasize ("without requiring cloud
infrastructure"), so the following substitutions were made. Each is
also documented as a comment at the top of the relevant file:

| Spec mentioned | This build uses | Why |
|---|---|---|
| PostgreSQL | **SQLite** (via Python's built-in `sqlite3`) | Matches the explicit "Configure SQLite database for local development" instruction in Milestone 2; needs no server. |
| Flask-SQLAlchemy ORM | Plain `sqlite3` wrapped in `models.py` classes with the same responsibilities (models, relationships, CRUD) | SQLAlchemy isn't installed and the app has no network access to install it; the data-access API is written so swapping in real SQLAlchemy later only touches `database/db.py` and `models.py`. |
| IBM Granite / Hugging Face Transformers for design generation | Rule-based `style_suggester.py`, `furniture_optimizer.py`, `budget_planner.py` using a curated interior-design knowledge base | No GPU/internet available to download multi-GB model weights; the tool *interface* (input → structured recommendation) is preserved so a real model can be dropped in later. |
| LangChain agent | `agents/interior_agent.py`, a hand-written orchestrator with the same contract (tools in, structured design out; chat text in, reply+action out) | No LLM API key/internet; intent parsing for the voice assistant uses keyword matching across English/Hindi/Telugu instead of an LLM. |
| Google Text-to-Speech (gTTS) | Browser-native **Web Speech API** (`SpeechRecognition` + `speechSynthesis`) in `static/js/voice.js` | Needs no server-side audio model or internet call from Flask; works fully client-side and still covers English/Hindi/Telugu. |
| Room dimensions from a photo | Heuristic estimate from image aspect ratio (clearly flagged `"estimated": true` in the API response) | True depth/size estimation from a single 2D photo needs specialized depth-estimation models or sensor data (LiDAR), which aren't available here. |
| AR furniture placement via WebRTC/ARKit-style plane detection | A simplified **tap-to-place colored overlay** on the live camera feed (`static/js/ar_viewer.js`), plus a three.js 3D room/furniture preview | True markerless AR needs WebXR device support that isn't guaranteed across browsers/OSes; this degrades gracefully anywhere `getUserMedia` works. |
| PDF export | Browser print-to-PDF (`window.print()`) | No server-side PDF engine (e.g. WeasyPrint) is installed/available offline. |
| Redis caching | Not implemented (listed under "Future Enhancements" in the original doc anyway) | Out of scope for a single-process local dev app; noted for future work. |

None of these change the **user-facing feature set** described in the
brief — every scenario (personalized AI design, AR visualization,
multilingual automated booking) works end-to-end — only the underlying
implementation technology, to keep the project runnable with zero
external services, API keys, or large downloads.

## 6. Database Schema

```
users        (id, username, email, password_hash, created_at)
designs      (id, user_id → users, room_type, style, budget, image_path,
              analysis_data JSON, design_data JSON, created_at, updated_at)
furniture    (id, design_id → designs, name, category, quantity,
              price_min, price_max, priority, image_url)
bookings     (id, design_id → designs, furniture_name, status,
              language, booking_date)
```
`users` 1—* `designs` 1—* `furniture`, `designs` 1—* `bookings`.

## 7. Security Notes (current state vs. "Future Enhancements" in spec)

Implemented: password hashing (Werkzeug's `generate_password_hash`),
server-side session auth, `secure_filename()` + extension allow-list on
uploads, parameterised SQL everywhere (no string-built queries).

Not yet implemented (see "Milestone 6: Future Enhancements" in the
original brief for the full list): CSRF tokens on forms, rate limiting,
two-factor authentication, and file-content validation beyond the
extension check. Add these before any real-world deployment.

## 8. Troubleshooting

- **Camera doesn't start**: most browsers require `localhost`/`127.0.0.1`
  or HTTPS for `getUserMedia`. Use `http://127.0.0.1:5000`, not your
  machine's LAN IP, unless you've set up HTTPS.
- **Voice assistant mic button does nothing**: `SpeechRecognition` is
  currently Chrome/Edge-only; Firefox/Safari support varies. Typing into
  the buddy chat box always works as a fallback.
- **`ModuleNotFoundError`**: make sure you activated the virtual
  environment and ran `pip install -r requirements.txt`.
- **Database looks empty/reset**: delete `database/designs.db` and
  restart `python app.py` to rebuild a fresh schema.
