import os
import streamlit as st
from datetime import datetime
from langchain_core.messages import HumanMessage
from main import app

st.set_page_config(
    page_title="AI Travel Booking System",
    page_icon="✈️",
    layout="wide"
)

# ── Theme ─────────────────────────────────────────────────────────────────────
# Dark is the default. Light mode is kept in the URL (?theme=light) so it survives a refresh.
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = st.query_params.get("theme") != "light"


def _sync_theme_param():
    if st.session_state.dark_mode:
        st.query_params.pop("theme", None)
    else:
        st.query_params["theme"] = "light"


PALETTES = {
    "dark": {
        "app-bg": "#080d14",
        "sidebar-bg": "#090e18",
        "sidebar-border": "#141f30",
        "surface": "#0e1623",
        "surface-alt": "#0e1a2b",
        "surface-sunken": "#0a1520",
        "card-bg": "#0e1a2e",
        "border": "#1e2e44",
        "border-alt": "#1a2e44",
        "border-card": "#1e3050",
        "text": "#cce0f5",
        "text-strong": "#e8f4ff",
        "heading": "#e0edf8",
        "text-sidebar": "#a0c4e0",
        "text-muted": "#7aa8cc",
        "text-save": "#8ab8d8",
        "accent-text": "#7ab8f5",
        "metric-val": "#4ea8f0",
        "link": "#4ea8f0",
        "placeholder": "#4a6a85",
        "placeholder-input": "#3a5570",
        "accent": "#3a7bd5",
        "focus-ring": "rgba(58,123,213,0.2)",
        "final-bg": "linear-gradient(160deg, #0c1a2e 0%, #0a1520 100%)",
        "final-border": "#1e3a5c",
        "download-bg": "#1a3a5c",
        "download-text": "#e8f4ff",
        "download-border": "#2a5080",
        "chip-bg": "#111b2b",
        "chip-bg-hover": "#1a2e47",
        "chip-text": "#f7fdf4",
        "toggle-off": "#4a6a85",
        "alert-bg": "#2a2410",
        "alert-border": "#5c4a14",
        "btn-shadow": "0 0 24px rgba(26,107,191,0.35), 0 4px 15px rgba(0,0,0,0.4)",
        "btn-shadow-hover": "0 0 40px rgba(26,107,191,0.6), 0 6px 20px rgba(0,0,0,0.5)",
    },
    "light": {
        "app-bg": "#f4f7fb",
        "sidebar-bg": "#e9eff6",
        "sidebar-border": "#d3deea",
        "surface": "#ffffff",
        "surface-alt": "#ffffff",
        "surface-sunken": "#f8fafd",
        "card-bg": "#ffffff",
        "border": "#d5e1ee",
        "border-alt": "#cbd9e8",
        "border-card": "#cbd9e8",
        "text": "#1f3347",
        "text-strong": "#0d2236",
        "heading": "#0d2236",
        "text-sidebar": "#2c4a66",
        "text-muted": "#4f6b85",
        "text-save": "#3d5f7f",
        "accent-text": "#1a5fa8",
        "metric-val": "#1a6bbf",
        "link": "#1565c0",
        "placeholder": "#7d93a8",
        "placeholder-input": "#7d93a8",
        "accent": "#3a7bd5",
        "focus-ring": "rgba(58,123,213,0.25)",
        "final-bg": "linear-gradient(160deg, #ffffff 0%, #f1f6fc 100%)",
        "final-border": "#cddcec",
        "download-bg": "#e3eefa",
        "download-text": "#0d2236",
        "download-border": "#b9d0ea",
        "chip-bg": "#ffffff",
        "chip-bg-hover": "#eef4fb",
        "chip-text": "#1f3347",
        "toggle-off": "#7d93a8",
        "alert-bg": "#fff6db",
        "alert-border": "#f0d78a",
        "btn-shadow": "0 0 18px rgba(26,107,191,0.22), 0 4px 12px rgba(13,34,54,0.12)",
        "btn-shadow-hover": "0 0 28px rgba(26,107,191,0.35), 0 6px 16px rgba(13,34,54,0.18)",
    },
}

_palette = PALETTES["dark" if st.session_state.dark_mode else "light"]
st.markdown(
    "<style>:root {" + "".join(f"--{name}: {value};" for name, value in _palette.items()) + "}</style>",
    unsafe_allow_html=True,
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, .stApp {
    font-family: 'Inter', sans-serif;
    background-color: var(--app-bg);
    color: var(--text);
}

/* ── Hero ── */
.hero-wrapper {
    position: relative;
    background: #080d14;  /* fixed dark backdrop: the photo doesn't span the full width */
    border-radius: 20px;
    overflow: hidden;
    margin-bottom: 2rem;
    height: 280px;
}
.hero-bg {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    filter: brightness(0.35);
    position: absolute;
    top: 0; left: 0;
}
.hero-content {
    position: relative;
    z-index: 2;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 2rem;
}
.hero-badge {
    background: rgba(58,123,213,0.25);
    border: 1px solid rgba(58,123,213,0.5);
    color: #7ab8f5 !important;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0.3rem 0.9rem;
    border-radius: 20px;
    margin-bottom: 0.9rem;
    display: inline-block;
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 0.6rem;
    line-height: 1.2;
}
.hero-sub {
    color: #94adc8;
    font-size: 1rem;
    max-width: 560px;
}

/* ── Input card ── */
.input-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.5rem;
}
.input-label {
    color: var(--accent-text);
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

/* ── Quick destinations ── */
.dest-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin: 0.8rem 0 1.2rem;
}
.dest-chip {
    background: var(--chip-bg);
    border: 1px solid var(--border-card);
    color: var(--chip-text);
    padding: 0.35rem 0.85rem;
    border-radius: 20px;
    font-size: 0.82rem;
    cursor: pointer;
    transition: all 0.2s;
}
.dest-chip:hover { background: var(--chip-bg-hover); border-color: var(--accent); color: var(--text-strong); }

/* ── Generate button ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #1a6bbf 0%, #0d4a8a 50%, #0a3d75 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.85rem 2.5rem !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.03em !important;
    width: 100% !important;
    box-shadow: var(--btn-shadow) !important;
    transition: all 0.3s ease !important;
}
div[data-testid="stButton"] > button:hover {
    box-shadow: var(--btn-shadow-hover) !important;
    transform: translateY(-2px) !important;
    background: linear-gradient(135deg, #2278d4 0%, #1057a0 50%, #0d4a8a 100%) !important;
}
div[data-testid="stButton"] > button:active {
    transform: translateY(0px) !important;
}

/* ── Agent result cards (st.status renders as an expander) ── */
[data-testid="stExpander"] details {
    background: var(--surface-sunken) !important;
    border: 1px solid var(--border-card) !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary {
    background: var(--card-bg) !important;
    border-radius: 12px 12px 0 0 !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary * { color: var(--heading) !important; }
[data-testid="stExpander"] hr { border-color: var(--border-card) !important; }

/* ── Section headers ── */
.sec-head {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 2rem 0 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}
.sec-head span { font-size: 1.15rem; font-weight: 600; color: var(--heading); }

/* ── Metric bar ── */
.metric-row {
    display: flex;
    gap: 1rem;
    margin: 1.5rem 0;
}
.metric-box {
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.metric-val { font-size: 1.8rem; font-weight: 700; color: var(--metric-val); }
.metric-lbl { font-size: 0.78rem; color: var(--text-muted) !important; margin-top: 0.2rem; text-transform: uppercase; letter-spacing: 0.08em; }

/* ── Final plan ── */
.final-card {
    background: var(--final-bg);
    border: 1px solid var(--final-border);
    border-left: 4px solid var(--accent);
    border-radius: 14px;
    padding: 1.8rem;
    line-height: 1.8;
    color: var(--text);
    font-size: 0.95rem;
}

/* ── Save bar ── */
.save-bar {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.85rem 1.2rem;
    color: var(--text-save) !important;
    font-size: 0.88rem;
    margin-top: 0.5rem;
}
.save-bar code { color: var(--accent-text) !important; background: var(--surface-sunken) !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--sidebar-bg) !important;
    border-right: 1px solid var(--sidebar-border) !important;
}
.sidebar-chip {
    background: var(--surface-alt);
    border: 1px solid var(--border-alt);
    border-radius: 8px;
    padding: 0.45rem 0.75rem;
    margin-bottom: 0.4rem;
    font-size: 0.83rem;
    color: var(--text-muted);
}
.sidebar-title { color: var(--heading); font-size: 1rem; font-weight: 600; margin: 1rem 0 0.5rem; }

/* Hide branding */
#MainMenu, footer, header { visibility: hidden; }

/* Textarea */
/* Text area and text input: Streamlit draws the border on a wrapper (…RootElement), so the
   border, background and focus ring go there and the inner field is borderless. */
[data-testid="stTextAreaRootElement"] {
    background: var(--surface-sunken) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
[data-testid="stTextInputRootElement"] {
    background: var(--surface-alt) !important;
    border: 1px solid var(--border-alt) !important;
    border-radius: 8px !important;
}
[data-testid="stTextAreaRootElement"]:focus-within,
[data-testid="stTextInputRootElement"]:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--focus-ring) !important;
}
.stTextArea textarea {
    background: transparent !important;
    border: none !important;
    color: var(--text-strong) !important;
    font-size: 0.95rem !important;
    resize: none !important;
}
.stTextArea textarea::placeholder { color: var(--placeholder) !important; }

/* Text input (sidebar User ID field) */
input[type="text"], .stTextInput input {
    background: transparent !important;
    border: none !important;
    color: var(--heading) !important;
}
input[type="text"]::placeholder { color: var(--placeholder-input) !important; }

/* Sidebar dark-mode toggle: Streamlit colours it from the device theme otherwise */
[data-testid="stCheckbox"] label > div:not([data-testid]) {
    background: var(--toggle-off) !important;
    border-color: var(--toggle-off) !important;
}
[data-testid="stCheckbox"] label:has(input:checked) > div:not([data-testid]) {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}
[data-testid="stCheckbox"] label > div:not([data-testid]) > div { background: #ffffff !important; }

/* Streamlit widget labels */
.stTextInput label, .stTextArea label,
.stSelectbox label, .stNumberInput label {
    color: var(--accent-text) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
}

/* General markdown / paragraph text */
.stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown th {
    color: var(--text) !important;
}
.stMarkdown td, .stMarkdown th { border-color: var(--border) !important; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 { color: var(--text-strong) !important; }
.stMarkdown a { color: var(--link) !important; }
.stMarkdown code {
    background: var(--surface-alt) !important;
    color: var(--accent-text) !important;
    padding: 0.15em 0.4em;
    border-radius: 4px;
}
hr { border-color: var(--border) !important; }

/* Streamlit warning ("Please describe your trip first"); its box is device-themed otherwise */
.stAlert { background: var(--surface-alt) !important; border-radius: 10px !important; }
[data-testid="stAlertContainer"] {
    background: var(--alert-bg) !important;
    border: 1px solid var(--alert-border) !important;
    border-radius: 10px !important;
}
.stAlert p, .stAlert div { color: var(--heading) !important; }

/* Sidebar text & dividers */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown { color: var(--text-sidebar) !important; }
section[data-testid="stSidebar"] hr { border-color: var(--border-alt) !important; }

/* Download button */
div[data-testid="stDownloadButton"] > button {
    background: var(--download-bg) !important;
    color: var(--download-text) !important;
    border: 1px solid var(--download-border) !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.toggle("🌙 Dark mode", key="dark_mode", on_change=_sync_theme_param)
    st.markdown("<div class='sidebar-title'>🌍 AI Travel Planner</div>", unsafe_allow_html=True)
    st.markdown("---")

    thread_id = st.text_input("👤 User ID", value="aarohi_user",
                              help="Your session ID — keeps travel history across queries")

    st.markdown("<div class='sidebar-title'>Powered by</div>", unsafe_allow_html=True)
    for tech in ["🔗 LangGraph", "🧠 Groq · GPT-OSS 120B", "🐘 PostgreSQL", "🔍 Tavily Search", "✈️ AviationStack"]:
        st.markdown(f"<div class='sidebar-chip'>{tech}</div>", unsafe_allow_html=True)

    st.markdown("<div class='sidebar-title'>Agent Pipeline</div>", unsafe_allow_html=True)
    for step in ["① Flight Agent", "② Hotel Agent", "③ Itinerary Agent", "④ Final Agent"]:
        st.markdown(f"<div class='sidebar-chip'>{step}</div>", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrapper">
    <img class="hero-bg"
         src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1400&q=80"
         alt="airplane above clouds"/>
    <div class="hero-content">
        <div class="hero-badge">✦ Multi-Agent AI System</div>
        <div class="hero-title">✈️ AI Travel Booking System</div>
        <div class="hero-sub">Four specialized agents work together — searching flights, hotels, building an itinerary, and delivering your perfect trip plan.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Destination image strip ───────────────────────────────────────────────────
DESTINATIONS = [
    ("🇯🇵 Tokyo",     "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=300&q=70"),
    ("🇫🇷 Paris",     "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=300&q=70"),
    ("🇹🇭 Bangkok",   "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=300&q=70"),
    ("🇮🇹 Rome",      "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=300&q=70"),
    ("🇦🇪 Dubai",     "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=300&q=70"),
]

cols = st.columns(5)
for col, (name, img_url) in zip(cols, DESTINATIONS):
    with col:
        st.markdown(f"""
        <div style="border-radius:10px;overflow:hidden;position:relative;height:90px;cursor:pointer;">
            <img src="{img_url}" style="width:100%;height:100%;object-fit:cover;filter:brightness(0.55);" />
            <div style="position:absolute;bottom:8px;left:0;right:0;text-align:center;
                        color:#fff;font-size:0.8rem;font-weight:600;">{name}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Input ─────────────────────────────────────────────────────────────────────
st.markdown("<div class='input-label'>🗺️ Describe your trip</div>", unsafe_allow_html=True)

QUICK = ["7-day Japan under ₹2L", "Paris trip for 5 days", "Dubai weekend trip", "Bali backpacking 10 days"]
qcols = st.columns(len(QUICK))

# The text area is keyed so it keeps its value across reruns; quick-pick buttons
# write into its session state via a callback (runs before the rerun).
def _quick_fill(label):
    st.session_state["trip_query"] = label

for qc, label in zip(qcols, QUICK):
    with qc:
        st.button(label, key=f"q_{label}", on_click=_quick_fill, args=(label,))

user_query = st.text_area(
    "",
    key="trip_query",
    placeholder="e.g. Plan a complete 7-day Japan trip including flights, hotels and sightseeing under ₹2 lakhs",
    height=100,
    label_visibility="collapsed",
)

generate = st.button("🚀  Generate My Travel Plan", use_container_width=True)

# ── Agent pipeline ────────────────────────────────────────────────────────────
AGENT_META = {
    "flight_agent":    ("✈️", "Flight Agent"),
    "hotel_agent":     ("🏨", "Hotel Agent"),
    "itinerary_agent": ("🗓️", "Itinerary Agent"),
    "final_agent":     ("🧠", "Final Agent"),
}

if generate:
    if not user_query.strip():
        st.warning("Please describe your trip first.")
    else:
        config = {"configurable": {"thread_id": thread_id}}
        collected = {"flight_results": "", "hotel_results": "",
                     "itinerary": "", "final_response": "", "llm_calls": 0}

        st.markdown("---")
        st.markdown("<div class='sec-head'><span>🤖 Agent Pipeline — Live</span></div>",
                    unsafe_allow_html=True)

        for chunk in app.stream(
            {
                "messages": [HumanMessage(content=user_query)],
                "user_query": user_query,
                "flight_results": "",
                "hotel_results": "",
                "itinerary": "",
                "llm_calls": 0,
            },
            config=config,
            stream_mode="updates",
        ):
            for node_name, state_update in chunk.items():
                icon, label = AGENT_META.get(node_name, ("🔧", node_name))

                with st.status(f"{icon}  {label}", state="complete", expanded=True):
                    if node_name == "flight_agent":
                        text = state_update.get("flight_results", "")
                        collected["flight_results"] = text
                        st.markdown(text or "_No flight data returned._")

                    elif node_name == "hotel_agent":
                        text = state_update.get("hotel_results", "")
                        collected["hotel_results"] = text
                        st.markdown(text or "_No hotel data returned._")

                    elif node_name == "itinerary_agent":
                        text = state_update.get("itinerary", "")
                        collected["itinerary"] = text
                        st.markdown(text or "_No itinerary generated._")

                    elif node_name == "final_agent":
                        msgs = state_update.get("messages", [])
                        text = msgs[-1].content if msgs else ""
                        collected["final_response"] = text
                        st.markdown(text or "_No final response._")

                    collected["llm_calls"] = state_update.get("llm_calls", collected["llm_calls"])

        # Metrics
        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-box"><div class="metric-val">4</div><div class="metric-lbl">Agents Run</div></div>
            <div class="metric-box"><div class="metric-val">{collected['llm_calls']}</div><div class="metric-lbl">LLM Calls</div></div>
            <div class="metric-box"><div class="metric-val">✅</div><div class="metric-lbl">Status</div></div>
        </div>
        """, unsafe_allow_html=True)

        # Final plan card
        if collected["final_response"]:
            st.markdown("<div class='sec-head'><span>🧠 Final Travel Plan</span></div>",
                        unsafe_allow_html=True)
            st.markdown(f"<div class='final-card'>{collected['final_response']}</div>",
                        unsafe_allow_html=True)

        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"travel_plan_{timestamp}.md"
        save_dir = os.path.join(os.path.dirname(__file__), "travel_plans")
        os.makedirs(save_dir, exist_ok=True)

        file_content = f"""# Travel Plan
**Query:** {user_query}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**User ID:** {thread_id}

---

## ✈️ Flight Information
{collected['flight_results'] or 'N/A'}

---

## 🏨 Hotel Information
{collected['hotel_results'] or 'N/A'}

---

## 🗓️ Itinerary
{collected['itinerary'] or 'N/A'}

---

## 🧠 Final Travel Plan
{collected['final_response'] or 'N/A'}

---
*LLM Calls: {collected['llm_calls']}*
"""
        with open(os.path.join(save_dir, filename), "w", encoding="utf-8") as f:
            f.write(file_content)

        dl_col, info_col = st.columns([1, 3])
        with dl_col:
            st.download_button("⬇️ Download Plan", data=file_content,
                               file_name=filename, mime="text/markdown",
                               use_container_width=True)
        with info_col:
            st.markdown(f"<div class='save-bar'>📁 Auto-saved → <code>travel_plans/{filename}</code></div>",
                        unsafe_allow_html=True)
