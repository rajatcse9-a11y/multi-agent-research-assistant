import html
import io
import re

import streamlit as st

from pipeline import run_research_pipeline

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResearchMind",
    page_icon="🧭",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Styling (light, editorial look) ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Inter:wght@400;500;600&display=swap');

:root {
    --bg: #f6f3ec;
    --card: #ffffff;
    --ink: #1c1b18;
    --muted: #7a7566;
    --line: #e4dfd3;
    --accent: #3d4fe0;
    --good: #1f9d6b;
}

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif;
}
.stApp { background: var(--bg); }
.stApp p, .stApp li, .stApp span, .stApp label, .stApp h1, .stApp h2,
.stApp h3, .stApp h4, .stApp td, .stApp th { color: var(--ink); }

#MainMenu, footer, header { visibility: hidden; }
.block-container { max-width: 980px; padding: 2.5rem 1.5rem 4rem; }

/* ── Hero ── */
.hero { text-align: center; padding: 1.5rem 0 1rem; }
.badge {
    display: inline-block;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--accent);
    background: rgba(61,79,224,0.08);
    border-radius: 999px;
    padding: 0.35rem 0.9rem;
    margin-bottom: 1rem;
}
.hero h1 {
    font-family: 'Fraunces', serif;
    font-size: clamp(2.4rem, 5vw, 3.6rem);
    font-weight: 700; line-height: 1.05; letter-spacing: -0.02em;
    margin: 0 0 0.8rem; color: var(--ink);
}
.hero h1 em { font-style: italic; color: var(--accent); }
.hero p {
    color: var(--muted); font-size: 1.02rem; line-height: 1.6;
    max-width: 540px; margin: 0 auto;
}

/* ── Search bar ── */
.st-key-search_bar {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 1rem 1.2rem 0.4rem;
    margin-top: 1.5rem;
    box-shadow: 0 6px 24px rgba(28,27,24,0.05);
}
.stTextInput input {
    background: #faf8f3 !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
    border-radius: 10px !important;
    padding: 0.7rem 0.9rem !important;
    font-size: 1rem !important;
}
.stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(61,79,224,0.15) !important;
}
.stTextInput input::placeholder { color: #a9a493 !important; }

.st-key-run_btn button {
    background: var(--ink) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    height: 2.9rem;
    font-weight: 600 !important;
    transition: background 0.15s, transform 0.15s !important;
}
.st-key-run_btn button p { color: #fff !important; }
.st-key-run_btn button:hover { background: var(--accent) !important; transform: translateY(-1px); }
.st-key-run_btn button:disabled { background: #b9b4a5 !important; }

/* ── Chips ── */
[class*="st-key-chip_"] button {
    background: transparent !important;
    border: 1px dashed #cfc9b8 !important;
    color: var(--muted) !important;
    border-radius: 999px !important;
    font-size: 0.78rem !important;
    padding: 0.15rem 0.8rem !important;
    min-height: 0 !important;
}
[class*="st-key-chip_"] button p { color: var(--muted) !important; font-size: 0.78rem !important; }
[class*="st-key-chip_"] button:hover { border-color: var(--accent) !important; }
[class*="st-key-chip_"] button:hover p { color: var(--accent) !important; }

/* ── Stepper ── */
.stepper {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 12px; margin: 1.6rem 0 1.2rem;
}
.step {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.9rem 1rem;
    transition: all 0.25s;
}
.step .top { display: flex; align-items: center; gap: 0.65rem; }
.step .dot {
    width: 28px; height: 28px; border-radius: 50%;
    display: grid; place-items: center;
    font-size: 0.75rem; font-weight: 600;
    background: #efeadf; color: var(--muted);
    flex-shrink: 0;
}
.step .name { font-weight: 600; font-size: 0.9rem; }
.step .desc { font-size: 0.76rem; color: var(--muted); margin: 0.45rem 0 0.35rem; line-height: 1.4; }
.step .state { font-size: 0.68rem; font-weight: 600; letter-spacing: 0.08em; color: #aaa595; }
.step.running { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(61,79,224,0.12); }
.step.running .dot { background: var(--accent); color: #fff; animation: pulse 1.2s infinite; }
.step.running .state { color: var(--accent); }
.step.done { border-color: rgba(31,157,107,0.5); }
.step.done .dot { background: var(--good); color: #fff; }
.step.done .state { color: var(--good); }
@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(61,79,224,0.45); }
    70%  { box-shadow: 0 0 0 8px rgba(61,79,224,0); }
    100% { box-shadow: 0 0 0 0 rgba(61,79,224,0); }
}
@media (max-width: 720px) { .stepper { grid-template-columns: repeat(2, 1fr); } }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { padding: 0.6rem 1rem; font-weight: 500; }
.stTabs [aria-selected="true"] p { color: var(--accent) !important; font-weight: 600; }
.stTabs [data-baseweb="tab-highlight"] { background: var(--accent) !important; }

/* ── Cards ── */
.st-key-report_card, .st-key-critic_card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 1.6rem 2rem;
    margin-top: 1rem;
    box-shadow: 0 6px 24px rgba(28,27,24,0.04);
}
.score-badge {
    display: inline-flex; align-items: baseline; gap: 0.3rem;
    background: rgba(31,157,107,0.1); color: var(--good);
    border-radius: 12px; padding: 0.5rem 1rem; margin-bottom: 0.8rem;
}
.score-badge b { font-family: 'Fraunces', serif; font-size: 2rem; color: var(--good); }
.score-badge span { color: var(--good) !important; font-weight: 500; }

.raw {
    white-space: pre-wrap; font-size: 0.85rem; line-height: 1.7;
    color: #4a463b; background: #faf8f3;
    border: 1px solid var(--line); border-radius: 10px; padding: 1rem 1.2rem;
}

.stDownloadButton button {
    background: var(--card) !important;
    border: 1px solid var(--line) !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
}
.stDownloadButton button:hover { border-color: var(--accent) !important; }

.footer { text-align: center; color: #a9a493; font-size: 0.74rem; margin-top: 3rem; }
</style>
""", unsafe_allow_html=True)


# ── Constants & helpers ──────────────────────────────────────────────────────
STEPS = [
    ("search", "Search", "Finds recent sources on the web"),
    ("reader", "Reader", "Scrapes the best page in depth"),
    ("writer", "Writer", "Drafts the structured report"),
    ("critic", "Critic", "Reviews and scores the draft"),
]
STATE_LABEL = {"waiting": "WAITING", "running": "RUNNING", "done": "DONE"}


def render_pipeline(active: str | None = None):
    """Stepper ko placeholder mein redraw karta hai (live progress ke liye)."""
    res = st.session_state.results
    cards = ""
    for i, (key, name, desc) in enumerate(STEPS, start=1):
        if key in res:
            state, dot = "done", "✓"
        elif key == active:
            state, dot = "running", str(i)
        else:
            state, dot = "waiting", str(i)
        cards += (
            f'<div class="step {state}">'
            f'<div class="top"><div class="dot">{dot}</div><div class="name">{name}</div></div>'
            f'<div class="desc">{desc}</div>'
            f'<div class="state">{STATE_LABEL[state]}</div>'
            f'</div>'
        )
    pipeline_slot.markdown(f'<div class="stepper">{cards}</div>', unsafe_allow_html=True)


def set_topic(text: str):
    st.session_state.topic_input = text


def extract_score(text: str):
    m = re.search(r"Score:\s*\**\s*(\d+(?:\.\d+)?)\s*/\s*10", text, re.IGNORECASE)
    return m.group(1) if m else None


# ── Download helpers ─────────────────────────────────────────────────────────
def to_plain_text(md: str) -> str:
    md = re.sub(r"^#+\s*", "", md, flags=re.MULTILINE)
    return md.replace("**", "").replace("__", "")


def _add_runs(paragraph, text: str):
    # **bold** ko bold run bana deta hai
    for part in re.split(r"(\*\*[^*]+\*\*)", text):
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            paragraph.add_run(part[2:-2]).bold = True
        elif part:
            paragraph.add_run(part)


def make_docx(title: str, md: str) -> bytes:
    from docx import Document  # pip install python-docx

    doc = Document()
    doc.add_heading(title, 0)
    for line in md.splitlines():
        s = line.strip()
        if not s or s.startswith("---"):
            continue
        h = re.match(r"^(#{1,4})\s+(.*)", s)
        if h:
            doc.add_heading(h.group(2).replace("**", ""), level=len(h.group(1)))
        elif re.match(r"^[-*•]\s+", s):
            _add_runs(doc.add_paragraph(style="List Bullet"), re.sub(r"^[-*•]\s+", "", s))
        elif re.match(r"^\d+[.)]\s+", s):
            _add_runs(doc.add_paragraph(style="List Number"), re.sub(r"^\d+[.)]\s+", "", s))
        else:
            _add_runs(doc.add_paragraph(), s)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def make_html(title: str, md: str) -> str:
    # markdown library ho to achhi HTML banti hai, warna simple fallback
    try:
        import markdown
        body = markdown.markdown(md, extensions=["tables", "fenced_code"])
    except ImportError:
        body = "<pre style='white-space:pre-wrap'>" + html.escape(md) + "</pre>"
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title>"
        "<style>body{font-family:Arial,sans-serif;max-width:800px;margin:40px auto;"
        "padding:0 16px;line-height:1.6;color:#222}"
        "table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:6px 10px}"
        "</style></head><body>"
        f"<h1>{html.escape(title)}</h1>{body}</body></html>"
    )


# ── Session state ────────────────────────────────────────────────────────────
for k, v in {
    "results": {},
    "running": False,
    "done": False,
    "topic_val": "",
    "error": None,
    "warnings": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="badge">Multi-agent research assistant</div>
    <h1>Research<em>Mind</em></h1>
    <p>Type a topic. Agents search the web, read the best source, write a structured
    report and a critic scores it, all in one go.</p>
</div>
""", unsafe_allow_html=True)


# ── Search bar ───────────────────────────────────────────────────────────────
with st.container(key="search_bar"):
    c1, c2 = st.columns([5, 1.6], vertical_alignment="center")
    with c1:
        topic = st.text_input(
            "Research topic",
            placeholder="e.g. Enter the topic",
            key="topic_input",
            label_visibility="collapsed",
            disabled=st.session_state.running,
        )
    with c2:
        run_btn = st.button(
            "Run research →",
            key="run_btn",
            use_container_width=True,
            disabled=st.session_state.running,
        )

    examples = ["LLM agents 2026", "CRISPR gene editing", "Fusion energy progress"]
    chip_cols = st.columns([1, 1, 1, 1.2])
    for i, ex in enumerate(examples):
        with chip_cols[i]:
            st.button(
                ex,
                key=f"chip_{i}",
                on_click=set_topic,
                args=(ex,),
                disabled=st.session_state.running,
            )

# ── Pipeline stepper ─────────────────────────────────────────────────────────
pipeline_slot = st.empty()
render_pipeline()


# ── Button handler ───────────────────────────────────────────────────────────
if run_btn:
    if not topic.strip():
        st.warning("Please enter a research topic first.")
    else:
        st.session_state.results = {}
        st.session_state.running = True
        st.session_state.done = False
        st.session_state.error = None
        st.session_state.warnings = []
        st.session_state.topic_val = topic.strip()
        st.rerun()


# ── Run pipeline ─────────────────────────────────────────────────────────────
if st.session_state.running and not st.session_state.done:
    topic_val = st.session_state.topic_val

    def on_step(step: str):
        render_pipeline(step)

    def on_result(step: str, output: str):
        st.session_state.results[step] = output

    try:
        with st.spinner("Pipeline is running, progress is shown in the steps above…"):
            final = run_research_pipeline(topic_val, on_step=on_step, on_result=on_result)

        if "error" in final:
            err = final["error"]
            st.session_state.error = f"'{err['step']}' step fail hua: {err['message']}"
        else:
            st.session_state.done = True
        st.session_state.warnings = final.get("warnings", [])
    except Exception as e:
        st.session_state.error = f"{type(e).__name__}: {e}"
    finally:
        st.session_state.running = False

    st.rerun()


# ── Errors / warnings ────────────────────────────────────────────────────────
for w in st.session_state.warnings:
    st.warning(w)
if st.session_state.error:
    st.error(f"Pipeline failed— {st.session_state.error}")


# ── Results (tabs) ───────────────────────────────────────────────────────────
r = st.session_state.results

if r:
    tab_report, tab_critic, tab_data = st.tabs(["📝 Report", "🧐 Critic review", "🔎 Research data"])

    with tab_report:
        if "writer" in r:
            with st.container(key="report_card"):
                st.markdown(r["writer"])

            # ── Download options ──
            st.markdown("##### ⬇ Download report")
            include_critic = st.checkbox("Critic feedback bhi add karo", value=False, key="inc_critic")

            full_md = r["writer"]
            if include_critic and r.get("critic"):
                full_md += "\n\n---\n\n## Critic feedback\n\n" + r["critic"]

            title = st.session_state.topic_val or "Research report"
            fname = re.sub(r"[^a-zA-Z0-9]+", "_", title)[:40].strip("_") or "report"

            d1, d2, d3, d4 = st.columns(4)
            d1.download_button(
                "Markdown (.md)", data=full_md, file_name=f"{fname}.md",
                mime="text/markdown", key="dl_md", use_container_width=True,
            )
            d2.download_button(
                "Text (.txt)", data=to_plain_text(full_md), file_name=f"{fname}.txt",
                mime="text/plain", key="dl_txt", use_container_width=True,
            )
            try:
                d3.download_button(
                    "Word (.docx)", data=make_docx(title, full_md), file_name=f"{fname}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="dl_docx", use_container_width=True,
                )
            except ImportError:
                d3.caption("Word ke liye: pip install python-docx")
            d4.download_button(
                "HTML (→ PDF)", data=make_html(title, full_md), file_name=f"{fname}.html",
                mime="text/html", key="dl_html", use_container_width=True,
            )
            st.caption("PDF chahiye to HTML file browser mein kholo aur Ctrl+P → Save as PDF.")
        else:
            st.info("Report abhi available nahi hai.")

    with tab_critic:
        if "critic" in r:
            with st.container(key="critic_card"):
                score = extract_score(r["critic"])
                if score:
                    st.markdown(
                        f'<div class="score-badge"><b>{html.escape(score)}</b><span>/ 10</span></div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(r["critic"])
        else:
            st.info("Critic review abhi available nahi hai.")

    with tab_data:
        if "search" in r:
            with st.expander("Search agent output", expanded=False):
                st.markdown(f'<div class="raw">{html.escape(str(r["search"]))}</div>',
                            unsafe_allow_html=True)
        if "reader" in r:
            with st.expander("Reader agent output (scraped content)", expanded=False):
                st.markdown(f'<div class="raw">{html.escape(str(r["reader"]))}</div>',
                            unsafe_allow_html=True)


st.markdown('<div class="footer">ResearchMind · LangChain agents · Streamlit</div>',
            unsafe_allow_html=True)