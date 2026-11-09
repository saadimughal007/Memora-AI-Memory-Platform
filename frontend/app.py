from __future__ import annotations

import html
import json
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
import streamlit as st


# ============================================================
# MEMORA — PREMIUM AI MEMORY PLATFORM
# Single-file Streamlit frontend. Existing FastAPI contract kept.
# ============================================================

st.set_page_config(
    page_title="MEMORA | Personal Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_API = "http://127.0.0.1:8000/api"
REQUEST_TIMEOUT = 120

THEMES: dict[str, dict[str, str]] = {
    "Obsidian Emerald": {
        "bg": "#080C0B", "sidebar": "#0B1511", "panel": "#101B16",
        "panel2": "#14251D", "accent": "#D6B56D", "accent_soft": "#F0DCA5",
        "green": "#9BE564", "text": "#F3F5F2", "muted": "#A6B2AA",
        "border": "rgba(214,181,109,.20)", "glow": "rgba(24,112,73,.22)",
    },
    "Champagne Gold": {
        "bg": "#0B0B0A", "sidebar": "#11100D", "panel": "#191713",
        "panel2": "#242017", "accent": "#E0C27B", "accent_soft": "#F5E6B8",
        "green": "#9ABF83", "text": "#F6F2E8", "muted": "#B6AE9D",
        "border": "rgba(224,194,123,.23)", "glow": "rgba(177,137,55,.17)",
    },
    "Parrot Luxe": {
        "bg": "#07100B", "sidebar": "#0A1810", "panel": "#102117",
        "panel2": "#173021", "accent": "#D6B56D", "accent_soft": "#F0DCA5",
        "green": "#9BE564", "text": "#F1F7EF", "muted": "#A5B9A6",
        "border": "rgba(155,229,100,.20)", "glow": "rgba(95,190,69,.20)",
    },
    "Midnight": {
        "bg": "#090D13", "sidebar": "#101722", "panel": "#151F2B",
        "panel2": "#1C2A38", "accent": "#D6B56D", "accent_soft": "#F0DCA5",
        "green": "#78D9B0", "text": "#F2F5F6", "muted": "#A4B1BC",
        "border": "rgba(160,183,193,.18)", "glow": "rgba(62,132,119,.18)",
    },
}


def init_state() -> None:
    defaults = {
        "session_id": str(uuid.uuid4()),
        "user_id": "local-user",
        "messages": [],
        "api_base": DEFAULT_API,
        "last_error": None,
        "theme": "Obsidian Emerald",
        "search_results": None,
        "last_backend_check": None,
        "last_memory_count": None,
        "page": "AI Workspace",
        "confirm_delete_all_memories": False,
        "pending_prompt": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


def inject_css(theme_name: str) -> None:
    t = THEMES.get(theme_name, THEMES["Obsidian Emerald"])
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
        :root {{
          --bg:{t['bg']}; --sidebar:{t['sidebar']}; --panel:{t['panel']};
          --panel2:{t['panel2']}; --gold:{t['accent']}; --gold-soft:{t['accent_soft']};
          --green:{t['green']}; --text:{t['text']}; --muted:{t['muted']};
          --border:{t['border']}; --glow:{t['glow']};
        }}
        html, body, [class*="css"] {{ font-family:'DM Sans',Inter, sans-serif; }}
        .stApp {{
          color:var(--text);
          background:
            radial-gradient(ellipse at 58% -12%, var(--glow), transparent 43%),
            radial-gradient(ellipse at 100% 55%, rgba(214,181,109,.045), transparent 34%),
            var(--bg);
        }}
        [data-testid="stHeader"] {{ background:rgba(8,12,11,.78); }}
        [data-testid="stSidebar"] {{
          background:linear-gradient(180deg,var(--sidebar),var(--bg));
          border-right:1px solid var(--border);
        }}
        [data-testid="stSidebar"] > div {{ padding:1.2rem .85rem 1.5rem; }}
        .block-container {{
          max-width:1780px; padding:1.6rem clamp(1rem,2.5vw,2.8rem) 3rem;
        }}
        h1,h2,h3,h4 {{ font-family:'Manrope',Inter,sans-serif; color:var(--text); letter-spacing:-.035em; }}
        p, label, [data-testid="stMarkdownContainer"] {{ color:var(--text); }}
        small,.stCaption {{ color:var(--muted)!important; }}
        .brand {{
          font:800 1.55rem 'Manrope',sans-serif; letter-spacing:.16em;
          color:var(--text); padding:.25rem .3rem .1rem;
        }}
        .brand-mark {{ color:var(--gold); }}
        .brand-sub {{
          color:var(--muted); font-size:.61rem; letter-spacing:.17em;
          font-weight:700; padding:.15rem .35rem .9rem;
        }}
        .side-label {{
          color:var(--muted); font-size:.64rem; font-weight:700;
          letter-spacing:.16em; text-transform:uppercase; margin:.7rem .35rem .45rem;
        }}
        .hero {{
          position:relative; overflow:hidden; border:1px solid var(--border);
          border-radius:22px; padding:clamp(1.35rem,2.4vw,2.25rem);
          background:linear-gradient(112deg,rgba(16,27,22,.98),rgba(13,27,20,.82) 58%,rgba(20,37,29,.72));
          box-shadow:0 22px 65px rgba(0,0,0,.22); animation:rise .45s ease both;
        }}
        .hero:after {{
          content:""; position:absolute; width:340px;height:340px;right:-100px;top:-190px;
          border-radius:50%; background:var(--glow); filter:blur(22px); pointer-events:none;
        }}
        .eyebrow {{ color:var(--gold); font-size:.68rem; letter-spacing:.2em; font-weight:800; text-transform:uppercase; }}
        .hero-title {{ font:800 clamp(1.8rem,3.3vw,3.05rem) 'Manrope',sans-serif; margin:.55rem 0 .35rem; line-height:1.12; }}
        .hero-copy {{ color:var(--muted); max-width:780px; font-size:.94rem; line-height:1.7; }}
        .hero-chip {{
          display:inline-block; margin-top:1rem; padding:.38rem .7rem; border-radius:30px;
          color:var(--gold-soft); border:1px solid var(--border); background:rgba(214,181,109,.06);
          font-size:.68rem; letter-spacing:.08em;
        }}
        .section-head {{ margin:.15rem 0 .1rem; font:750 1.28rem 'Manrope',sans-serif; }}
        .section-copy {{ color:var(--muted); font-size:.83rem; margin-bottom:1rem; }}
        .metric {{
          min-height:116px; padding:1rem 1.05rem; border-radius:16px;
          border:1px solid var(--border);
          background:linear-gradient(145deg,var(--panel2),var(--panel));
          box-shadow:0 12px 32px rgba(0,0,0,.13);
          transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease;
        }}
        .metric:hover {{ transform:translateY(-3px); border-color:var(--gold); box-shadow:0 15px 35px var(--glow); }}
        .metric-label {{ color:var(--muted); text-transform:uppercase; font-size:.65rem; letter-spacing:.13em; font-weight:800; }}
        .metric-value {{ color:var(--text); font:800 clamp(1.35rem,2vw,1.85rem) 'Manrope',sans-serif; margin-top:.55rem; }}
        .metric-note {{ color:var(--muted); font-size:.7rem; margin-top:.18rem; }}
        .metric-icon {{ float:right; color:var(--gold); font-size:1.1rem; }}
        .panel {{
          background:linear-gradient(145deg,var(--panel),rgba(14,25,19,.86));
          border:1px solid var(--border); border-radius:17px; padding:1.05rem 1.15rem;
        }}
        .memory-card {{
          background:linear-gradient(145deg,var(--panel),var(--panel2));
          border:1px solid var(--border); border-radius:15px; padding:1rem 1.1rem;
          margin:.55rem 0; transition:transform .2s ease,border-color .2s ease;
        }}
        .memory-card:hover {{ transform:translateY(-2px); border-color:var(--gold); }}
        .memory-content {{ color:var(--text); line-height:1.65; white-space:pre-wrap; overflow-wrap:anywhere; }}
        .memory-meta {{ color:var(--muted); font-size:.72rem; margin-top:.7rem; }}
        .pill {{ display:inline-block; border:1px solid var(--border); color:var(--gold-soft);
          background:rgba(214,181,109,.055); padding:.18rem .55rem; border-radius:99px;
          font-size:.66rem; margin-right:.3rem; }}
        div[data-testid="stChatMessage"] {{
          background:linear-gradient(145deg,var(--panel),rgba(14,25,19,.9));
          border:1px solid var(--border); border-radius:17px; padding:.75rem .95rem;
          animation:rise .24s ease both;
        }}
        .stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {{
          border-radius:10px; border:1px solid var(--border); min-height:2.55rem;
          font-weight:650; transition:all .18s ease;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
          border-color:var(--gold); color:var(--gold-soft); transform:translateY(-1px);
          box-shadow:0 7px 22px var(--glow);
        }}
        .stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button {{
          background:linear-gradient(110deg,#B9944D,#D6B56D); color:#15130D; border:0;
        }}
        [data-testid="stRadio"] label {{ padding:.4rem .5rem; border-radius:9px; }}
        [data-testid="stRadio"] label:hover {{ background:rgba(214,181,109,.08); }}
        [data-testid="stTabs"] button {{ font-weight:650; }}
        [data-testid="stExpander"] {{ border:1px solid var(--border); border-radius:12px; background:rgba(16,27,22,.48); }}
        [data-testid="stMetric"], [data-testid="stForm"], [data-testid="stDataFrame"] {{
          border:1px solid var(--border); border-radius:14px;
        }}
        input,textarea {{ border-radius:9px!important; }}
        [data-testid="stProgressBar"] > div > div {{ background:var(--green); }}
        hr {{ border-color:var(--border); }}
        .footer {{ text-align:center; color:var(--muted); font-size:.7rem; letter-spacing:.08em; padding:1.2rem; }}
        .empty {{
          border:1px dashed var(--border); border-radius:16px; padding:2rem 1rem;
          text-align:center; color:var(--muted); background:rgba(16,27,22,.35);
        }}
        @keyframes rise {{ from {{opacity:0;transform:translateY(7px)}} to {{opacity:1;transform:translateY(0)}} }}
        @media(max-width:900px) {{
          .block-container {{ padding:1.2rem 1rem 2rem; }}
          .hero {{ padding:1.25rem; }}
          .metric {{ min-height:100px; }}
        }}
        @media(max-width:600px) {{
          .block-container {{ padding:.8rem .65rem 1.5rem; }}
          .hero-title {{ font-size:1.7rem; }}
          .metric {{ padding:.8rem; }}
        }}
        @media(prefers-reduced-motion:reduce) {{
          *,*::before,*::after {{ animation-duration:.01ms!important;transition-duration:.01ms!important;scroll-behavior:auto!important; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css(st.session_state.theme)


# ------------------------- API CLIENT -------------------------

def api_request(method: str, endpoint: str, **kwargs: Any) -> Any:
    base_url = str(st.session_state.api_base).rstrip("/")
    url = f"{base_url}/{endpoint.lstrip('/')}"
    try:
        response = requests.request(method=method, url=url, timeout=REQUEST_TIMEOUT, **kwargs)
        if not response.ok:
            try:
                body = response.json()
                detail = body.get("detail", body) if isinstance(body, dict) else body
            except ValueError:
                detail = response.text[:1000]
            raise RuntimeError(f"HTTP {response.status_code}: {detail}")
        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise RuntimeError("Backend returned an invalid JSON response.") from exc
    except requests.Timeout as exc:
        raise RuntimeError("Backend request timed out. Check the server and retry.") from exc
    except requests.ConnectionError as exc:
        raise RuntimeError(f"Cannot connect to backend at {url}. Check whether FastAPI is running.") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"API request failed: {exc}") from exc


def get_memories() -> list:
    result = api_request("GET", "/memories", params={"user_id": st.session_state.user_id})
    if result is None:
        return []
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        for key in ("memories", "items", "results"):
            if isinstance(result.get(key), list):
                return result[key]
    raise RuntimeError("Unexpected /memories response: expected a list of records.")


def set_error(exc: Any, title: str = "Request failed") -> None:
    st.session_state.last_error = str(exc)
    st.error(f"{title}: {exc}")


def safe_text(value: Any, fallback: str = "—") -> str:
    return str(value) if value is not None else fallback


def memory_fields(memory: Any) -> tuple[str, str, str, str]:
    if isinstance(memory, dict):
        return (
            safe_text(memory.get("content"), "No content"),
            safe_text(memory.get("id")),
            safe_text(memory.get("category"), "other"),
            safe_text(memory.get("importance")),
        )
    return str(memory), "—", "retrieved", "—"


def render_memory(memory: Any) -> None:
    content, memory_id, category, importance = memory_fields(memory)
    st.markdown(
        f"""<div class="memory-card"><div class="memory-content">{html.escape(content)}</div>
        <div class="memory-meta"><span class="pill">{html.escape(category)}</span>
        ID: {html.escape(memory_id)} &nbsp;·&nbsp; Importance: {html.escape(importance)}</div></div>""",
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: Any, note: str = "", icon: str = "✦") -> None:
    st.markdown(
        f"""<div class="metric"><span class="metric-icon">{html.escape(icon)}</span>
        <div class="metric-label">{html.escape(str(label))}</div>
        <div class="metric-value">{html.escape(str(value))}</div>
        <div class="metric-note">{html.escape(str(note))}</div></div>""",
        unsafe_allow_html=True,
    )


def importance_number(value: Any) -> int | None:
    return int(value) if isinstance(value, (int, float)) else None


# ------------------------- SIDEBAR NAVIGATION -------------------------

with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">✦</span> MEMORA</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">PERSONAL INTELLIGENCE SYSTEM</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-label">Workspace</div>', unsafe_allow_html=True)

    pages = ["AI Workspace", "Memory Center", "Analytics", "System Monitor", "Documentation"]
    page_icons = {"AI Workspace": "◈", "Memory Center": "▤", "Analytics": "▥", "System Monitor": "⌁", "Documentation": "▧"}
    selected_page = st.radio(
        "Main navigation", pages,
        index=pages.index(st.session_state.page) if st.session_state.page in pages else 0,
        format_func=lambda page: f"{page_icons[page]}   {page}",
        label_visibility="collapsed",
        key="main_navigation",
    )
    st.session_state.page = selected_page

    st.markdown('<div class="side-label">Appearance</div>', unsafe_allow_html=True)
    selected_theme = st.selectbox(
        "Visual theme", list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.theme),
        label_visibility="collapsed", key="theme_picker",
    )
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

    st.markdown('<div class="side-label">Workspace settings</div>', unsafe_allow_html=True)
    st.session_state.user_id = st.text_input("User ID", value=st.session_state.user_id).strip() or "local-user"
    st.text_input("Backend API URL", key="api_base")
    st.caption("Current session")
    st.code(st.session_state.session_id, language=None)

    if st.button("＋  New conversation", use_container_width=True, key="new_conversation"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    if st.button("Clear current session", use_container_width=True, key="clear_session"):
        try:
            api_request("DELETE", f"/sessions/{st.session_state.session_id}")
            st.session_state.messages = []
            st.success("Session cleared.")
            st.rerun()
        except Exception as exc:
            set_error(exc, "Session clear failed")

    st.markdown('<div class="side-label">Platform</div>', unsafe_allow_html=True)
    st.caption("FastAPI  ·  Gemini  ·  SQLite  ·  ChromaDB")
    st.caption("MEMORA / LOCAL WORKSPACE")


# ------------------------- LIVE BACKEND DATA -------------------------

try:
    memories = get_memories()
    memory_load_error = None
    st.session_state.last_memory_count = len(memories)
except Exception as exc:
    memories = []
    memory_load_error = str(exc)

valid_memory_dicts = [m for m in memories if isinstance(m, dict)]
categories = Counter(safe_text(m.get("category"), "other") for m in valid_memory_dicts)
total_memories = len(memories)
high_importance = sum(
    1 for m in valid_memory_dicts
    if importance_number(m.get("importance")) is not None and importance_number(m.get("importance")) >= 4
)
importance_values = [
    importance_number(m.get("importance")) for m in valid_memory_dicts
    if importance_number(m.get("importance")) is not None
]
chat_message_count = len(st.session_state.messages)


# ------------------------- GLOBAL HERO -------------------------

st.markdown(
    """<div class="hero">
      <div class="eyebrow">Your personal intelligence layer</div>
      <div class="hero-title">Think Better. Remember Everything.</div>
      <div class="hero-copy">An intelligent memory infrastructure that helps AI understand,
      remember, and evolve with every interaction. One connected workspace for conversations,
      long-term knowledge and semantic recall.</div>
      <span class="hero-chip">OBSIDIAN EMERALD &nbsp; × &nbsp; CHAMPAGNE GOLD</span>
    </div>""",
    unsafe_allow_html=True,
)
st.write("")


# ------------------------- DASHBOARD OVERVIEW -------------------------

top_metrics = st.columns(4, gap="medium")
with top_metrics[0]:
    metric_card("Stored memories", total_memories if not memory_load_error else "—",
                "Live backend records" if not memory_load_error else "Backend data unavailable", "◈")
with top_metrics[1]:
    metric_card("Chat messages", chat_message_count, "This browser conversation only", "✧")
with top_metrics[2]:
    metric_card("High importance", high_importance if not memory_load_error else "—",
                "Score ≥ 4 where numeric scores exist", "◆")
with top_metrics[3]:
    metric_card("Active workspace", "Online" if not memory_load_error else "Offline",
                st.session_state.theme, "⌁")

st.write("")


# ============================================================
# AI WORKSPACE
# ============================================================

if st.session_state.page == "AI Workspace":
    title_col, export_col = st.columns([4, 1])
    with title_col:
        st.markdown('<div class="section-head">◈ &nbsp; Conversation studio</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">A context-aware workspace connected to your existing long-term memory API.</div>', unsafe_allow_html=True)
    with export_col:
        if st.session_state.messages:
            export_data = {
                "session_id": st.session_state.session_id,
                "user_id": st.session_state.user_id,
                "messages": st.session_state.messages,
                "exported_at": datetime.now().isoformat(),
            }
            st.download_button(
                "⇩ Export JSON", data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name="memora_conversation.json", mime="application/json",
                use_container_width=True, key="export_conversation",
            )

    if not st.session_state.messages:
        st.markdown("**Start with a thought**")
        prompts = [
            "What do you remember about me?",
            "Remember that I prefer concise technical explanations.",
            "Summarize my active goals and projects.",
        ]
        prompt_cols = st.columns(3)
        for i, suggestion in enumerate(prompts):
            with prompt_cols[i]:
                if st.button(suggestion, key=f"quick_prompt_{i}", use_container_width=True):
                    st.session_state.pending_prompt = suggestion
                    st.rerun()

    for message in st.session_state.messages:
        role = message.get("role", "assistant")
        avatar = "👤" if role == "user" else "🧠"
        with st.chat_message(role, avatar=avatar):
            st.markdown(message.get("content", ""))
            retrieved = message.get("retrieved_memories") or []
            if role == "assistant" and retrieved:
                with st.expander(f"✧  Retrieved memories · {len(retrieved)}"):
                    for item in retrieved:
                        render_memory(item)

    prompt = st.chat_input("Message Memora…")
    if not prompt and st.session_state.pending_prompt:
        prompt = st.session_state.pop("pending_prompt")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar="🧠"):
            with st.spinner("Memora is thinking · retrieving context…"):
                try:
                    # Existing /chat payload is intentionally unchanged.
                    data = api_request(
                        "POST", "/chat",
                        json={
                            "session_id": st.session_state.session_id,
                            "user_id": st.session_state.user_id,
                            "message": prompt,
                        },
                    )
                    if not isinstance(data, dict) or not isinstance(data.get("answer"), str):
                        raise RuntimeError("Invalid /chat response: expected an 'answer' string.")
                    answer = data["answer"]
                    retrieved = data.get("retrieved_memories", [])
                    if not isinstance(retrieved, list):
                        retrieved = []
                    st.markdown(answer)
                    if retrieved:
                        with st.expander(f"✧  Retrieved memories · {len(retrieved)}"):
                            for item in retrieved:
                                render_memory(item)
                    st.session_state.messages.append({
                        "role": "assistant", "content": answer, "retrieved_memories": retrieved,
                    })
                    st.session_state.last_error = None
                except Exception as exc:
                    # A failed request is never persisted as a successful assistant message.
                    set_error(exc, "AI chat error")
        st.rerun()


# ============================================================
# MEMORY CENTER
# ============================================================

elif st.session_state.page == "Memory Center":
    st.markdown('<div class="section-head">▤ &nbsp; Memory center</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Curate, search and manage the knowledge Memora retains over time.</div>', unsafe_allow_html=True)

    create_col, search_col = st.columns(2, gap="large")
    with create_col:
        with st.container(border=True):
            st.markdown("#### ＋ Create a memory")
            with st.form("create_memory_form", clear_on_submit=True):
                new_content = st.text_area(
                    "Memory content",
                    placeholder="Example: I prefer practical explanations with concise steps.",
                    height=125,
                )
                new_category = st.selectbox(
                    "Category", ["preference", "goal", "background", "project", "other"],
                )
                new_importance = st.slider("Importance", 1, 5, 3)
                save_clicked = st.form_submit_button("Save memory", use_container_width=True)
            if save_clicked:
                if not new_content.strip():
                    st.warning("Enter memory content first.")
                else:
                    try:
                        # Existing /memories payload is intentionally unchanged.
                        api_request(
                            "POST", "/memories",
                            json={
                                "user_id": st.session_state.user_id,
                                "content": new_content.strip(),
                                "category": new_category,
                                "importance": new_importance,
                            },
                        )
                        st.success("Memory saved.")
                        st.rerun()
                    except Exception as exc:
                        set_error(exc, "Memory save failed")

    with search_col:
        with st.container(border=True):
            st.markdown("#### ⌕ Semantic memory search")
            query = st.text_input("Search by meaning", placeholder="e.g. What are my career goals?")
            limit = st.slider("Maximum results", 1, 20, 5)
            if st.button("Search memories", use_container_width=True, key="search_memories"):
                if not query.strip():
                    st.warning("Enter a search query.")
                else:
                    try:
                        result = api_request(
                            "GET", "/memories/search",
                            params={
                                "user_id": st.session_state.user_id,
                                "query": query.strip(),
                                "limit": limit,
                            },
                        )
                        if isinstance(result, dict):
                            found = result.get("results", [])
                        elif isinstance(result, list):
                            found = result
                        else:
                            found = []
                        st.session_state.search_results = found if isinstance(found, list) else []
                        st.session_state.last_error = None
                    except Exception as exc:
                        st.session_state.search_results = None
                        set_error(exc, "Semantic search failed")

    if st.session_state.search_results is not None:
        with st.container(border=True):
            st.markdown(f"#### Search results · {len(st.session_state.search_results)}")
            if not st.session_state.search_results:
                st.info("No matching memories were returned.")
            else:
                for item in st.session_state.search_results:
                    render_memory(item)
            if st.button("Clear search results", key="clear_search_results"):
                st.session_state.search_results = None
                st.rerun()

    st.divider()
    list_col, refresh_col = st.columns([4, 1])
    with list_col:
        st.markdown("#### Stored knowledge")
    with refresh_col:
        if st.button("↻ Refresh records", use_container_width=True, key="refresh_memories"):
            st.rerun()

    if memory_load_error:
        st.error(f"Could not load memories: {memory_load_error}")
    elif not memories:
        st.markdown('<div class="empty">◈<br><br>Your memory bank is waiting.<br>Create your first memory to begin building a persistent knowledge layer.</div>', unsafe_allow_html=True)
    else:
        filter_options = ["all"] + sorted(categories.keys())
        selected_category = st.selectbox("Filter category", filter_options, key="memory_category_filter")
        filtered = memories if selected_category == "all" else [
            item for item in memories
            if isinstance(item, dict) and safe_text(item.get("category"), "other") == selected_category
        ]
        st.caption(f"Showing {len(filtered)} of {total_memories} records")
        for index, item in enumerate(filtered):
            if not isinstance(item, dict):
                render_memory(item)
                continue
            content, memory_id, category, importance = memory_fields(item)
            with st.container(border=True):
                info_col, delete_col = st.columns([5, 1])
                with info_col:
                    st.markdown(f"**Memory · {html.escape(memory_id)}**")
                    st.write(content)
                    st.caption(f"Category: {category}  ·  Importance: {importance}/5")
                    score = importance_number(item.get("importance"))
                    if score is not None:
                        st.progress(max(0.0, min(1.0, score / 5)))
                with delete_col:
                    st.write("")
                    if memory_id != "—" and st.button("Delete", key=f"delete_memory_{memory_id}_{index}"):
                        try:
                            deletion = api_request(
                                "DELETE", f"/memories/{memory_id}",
                                params={"user_id": st.session_state.user_id},
                            )
                            if isinstance(deletion, dict) and deletion.get("deleted") is False:
                                st.warning("The backend reported that this memory was not found.")
                            else:
                                st.success("Delete request completed.")
                            st.rerun()
                        except Exception as exc:
                            set_error(exc, "Memory deletion failed")

    with st.expander("⚠ Danger zone · Delete all memories"):
        st.warning("This permanently deletes all long-term memories for the current User ID.")
        confirmed = st.checkbox(
            "I understand this action cannot be undone.",
            key="confirm_delete_all_memories",
        )
        if st.button("Permanently delete all memories", type="primary",
                     disabled=not confirmed, key="delete_all_memories"):
            try:
                deletion = api_request(
                    "DELETE", "/memories",
                    params={"user_id": st.session_state.user_id},
                )
                count = deletion.get("deleted_count") if isinstance(deletion, dict) else None
                st.success(
                    f"Delete request completed. Backend reported {count} deleted records."
                    if count is not None else "Delete request completed."
                )
                st.session_state.confirm_delete_all_memories = False
                st.rerun()
            except Exception as exc:
                set_error(exc, "Delete-all request failed")


# ============================================================
# ANALYTICS
# ============================================================

elif st.session_state.page == "Analytics":
    st.markdown('<div class="section-head">▥ &nbsp; Knowledge analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">A live view of the memory records returned by your existing backend.</div>', unsafe_allow_html=True)

    if memory_load_error:
        st.warning("Live analytics are unavailable because the backend memory request failed.")
    else:
        a, b, c, d = st.columns(4, gap="medium")
        with a:
            metric_card("Total memories", total_memories, "Backend records", "◈")
        with b:
            metric_card("Categories", len(categories), "Distinct categories", "▤")
        with c:
            metric_card("High importance", high_importance, "Numeric importance ≥ 4", "◆")
        with d:
            metric_card("Scored records", len(importance_values), "Numeric importance available", "✧")

        st.write("")
        chart_left, chart_right = st.columns(2, gap="large")
        with chart_left:
            with st.container(border=True):
                st.markdown("#### Memory category distribution")
                if categories:
                    st.bar_chart(dict(categories), use_container_width=True, color="#9BE564")
                else:
                    st.info("No category values available.")
        with chart_right:
            with st.container(border=True):
                st.markdown("#### Importance distribution")
                if importance_values:
                    importance_counts = Counter(importance_values)
                    st.bar_chart(
                        {str(score): importance_counts.get(score, 0) for score in range(1, 6)},
                        use_container_width=True, color="#D6B56D",
                    )
                else:
                    st.info("The API records do not contain numeric importance scores.")

        st.markdown("#### Category breakdown")
        if categories:
            for category, count in sorted(categories.items()):
                col1, col2, col3 = st.columns([2, 5, 1])
                with col1:
                    st.write(f"**{category.title()}**")
                with col2:
                    st.progress(count / total_memories if total_memories else 0)
                with col3:
                    st.write(count)
        else:
            st.info("No categories are available yet.")

        st.caption(
            "No memory-growth timeline or quality score is displayed because the supplied API "
            "response contract does not establish timestamp or quality fields."
        )

    st.divider()
    st.markdown("#### Conversation activity")
    metric_card("Messages in this browser session", len(st.session_state.messages),
                "Frontend session statistic — not a database-wide total", "✧")
    st.caption("This count is limited to the messages held in this browser session.")


# ============================================================
# SYSTEM MONITOR
# ============================================================

elif st.session_state.page == "System Monitor":
    st.markdown('<div class="section-head">⌁ &nbsp; System monitor</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Runtime visibility and backend connectivity without exposing credentials.</div>', unsafe_allow_html=True)

    status_col, refresh_col = st.columns([4, 1])
    with status_col:
        st.markdown("#### Backend connectivity")
        if memory_load_error:
            st.error("● Backend unavailable or memory request failed")
            st.caption(memory_load_error)
        else:
            st.success("● FastAPI backend responded successfully")
            st.caption("Connectivity verified through GET /memories.")
    with refresh_col:
        if st.button("↻ Refresh status", use_container_width=True, key="refresh_system_status"):
            try:
                api_request("GET", "/memories", params={"user_id": st.session_state.user_id})
                st.session_state.last_backend_check = datetime.now().isoformat(timespec="seconds")
                st.session_state.last_error = None
                st.success("Status refreshed.")
            except Exception as exc:
                set_error(exc, "Status refresh failed")
            st.rerun()

    st.divider()
    st.markdown("#### Runtime configuration")
    config_col, data_col = st.columns(2, gap="large")
    with config_col:
        with st.container(border=True):
            st.markdown("**Connection & identity**")
            st.code(
                "\n".join([
                    f"API base: {st.session_state.api_base}",
                    f"User ID: {st.session_state.user_id}",
                    f"Session ID: {st.session_state.session_id}",
                    f"Theme: {st.session_state.theme}",
                    f"Request timeout: {REQUEST_TIMEOUT}s",
                ]),
                language="text",
            )
    with data_col:
        with st.container(border=True):
            st.markdown("**Runtime statistics**")
            st.code(
                "\n".join([
                    f"Memory records loaded: {total_memories if not memory_load_error else 'Unavailable'}",
                    f"Frontend chat messages: {len(st.session_state.messages)}",
                    f"Last manual status refresh: {st.session_state.last_backend_check or 'Not manually refreshed'}",
                    "Backend: FastAPI",
                    "Storage: SQLite + ChromaDB (server-side)",
                ]),
                language="text",
            )

    st.info("Gemini API credentials and other secrets are intentionally not displayed in the frontend.")
    st.markdown("#### Application error log")
    if st.session_state.last_error:
        st.error(st.session_state.last_error)
        if st.button("Clear error log", key="clear_error_log"):
            st.session_state.last_error = None
            st.rerun()
    else:
        st.success("No recorded frontend API error.")



# ============================================================
# PROJECT DOCUMENTATION — reads the repository README.md
# ============================================================

elif st.session_state.page == "Documentation":
    st.markdown('<div class="section-head">▧ &nbsp; Project documentation</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">The project guide, architecture and setup instructions, shown from the repository README.</div>',
        unsafe_allow_html=True,
    )

    # frontend/app.py -> repository root -> README.md
    project_root = Path(__file__).resolve().parent.parent
    readme_path = project_root / "README.md"
    if readme_path.is_file():
        try:
            readme_text = readme_path.read_text(encoding="utf-8")
            st.caption(f"Source: {readme_path}")
            st.download_button(
                "⇩ Download README.md",
                data=readme_text,
                file_name="README.md",
                mime="text/markdown",
                key="download_project_readme",
            )
            st.markdown(readme_text)
        except OSError as exc:
            st.error(f"README.md exists but could not be read: {exc}")
    else:
        st.warning("README.md was not found at the project root.")
        st.markdown(
            """### Memora — Advanced AI Agent Memory System

**Give AI Agents a Memory That Lasts.**

Memora combines session-scoped short-term memory, persistent long-term memory,
semantic retrieval and Gemini-powered response generation.

#### Architecture

- **Streamlit:** user interface and conversational workspace.
- **FastAPI:** REST API and application orchestration.
- **SQLite:** persistent long-term memory records.
- **ChromaDB:** vector storage and semantic retrieval.
- **Sentence Transformers:** local embedding generation.
- **Google Gemini:** response generation and memory-related intelligence.

#### Main capabilities

1. Short-term conversational context within an active session.
2. Long-term user facts stored in SQLite.
3. Semantic memory retrieval using embeddings and ChromaDB.
4. Context construction from available memory layers.
5. Explicit memory requests rather than saving every conversation automatically.

#### Run locally

```powershell
uv sync
uv run uvicorn backend.main:app --reload
uv run streamlit run frontend/app.py
```

API documentation: `http://127.0.0.1:8000/docs`

> The project README is the source of truth for setup details and documented capabilities.
"""
        )



st.divider()
st.markdown(
    '<div class="footer">MEMORA &nbsp;·&nbsp; ADVANCED AI MEMORY PLATFORM<br>'
    'FASTAPI · GEMINI · SQLITE · CHROMADB · STREAMLIT</div>',
    unsafe_allow_html=True,
)
