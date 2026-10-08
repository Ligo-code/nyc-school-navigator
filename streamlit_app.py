"""Launch from the project root: uv run streamlit run streamlit_app.py."""

from html import escape

import streamlit as st


st.set_page_config(page_title="NYC School Navigator", layout="wide")
st.markdown("""
<style>
[data-testid="stMainBlockContainer"] {max-width: 1100px; padding-top: 2.8rem; padding-bottom: 3rem;}
h1 {font-family: Georgia, serif; font-weight: 500; letter-spacing: -.035em;}
h2, h3 {letter-spacing: -.025em;}
[data-testid="stSidebar"] {border-right: 1px solid #dfe5de;}
.eyebrow {color: #176b57; font-size: .75rem; letter-spacing: .09em; text-transform: uppercase; margin-bottom: .7rem;}
.subtitle {font-size: 1.15rem; color: #46534a; margin-bottom: 1.6rem;}
.school-card {border-top: 2px solid #c6d5cb; padding: .9rem 0; min-height: 105px;}
.school-card strong {font-size: .95rem; font-weight: 600; display: block; line-height: 1.45;}
.school-card span {font-size: .75rem; color: #647168; display: block; margin-top: .45rem; letter-spacing: .05em;}
[data-testid="stTextInput"] input {padding: .9rem; font-size: 1rem;}
@media (max-width: 640px) {
  [data-testid="stMainBlockContainer"] {padding-top: 1.5rem;}
  .school-card {min-height: 0;}
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.subheader("About")
    st.write(
        "This prototype compares three NYC middle schools using 2024–25 NYC "
        "School Quality Report data. Answers are generated locally from retrieved school data."
    )
    st.divider()
    st.caption("Data · NYC School Quality Report")
    st.caption("Retrieval · MiniLM embeddings")
    st.caption("Generation · Qwen3 4B · local")
    st.caption("Storage · MongoDB")

st.markdown('<div class="eyebrow">2024–25 School Quality Report · 3 schools</div>', unsafe_allow_html=True)
st.title("NYC School Navigator")
st.markdown('<p class="subtitle">Compare NYC middle schools using official school quality data.</p>', unsafe_allow_html=True)

schools = [
    ("The Christa McAuliffe School / I.S. 187", "20K187"),
    ("David A. Boody / I.S. 228", "21K228"),
    ("Mark Twain / I.S. 239", "21K239"),
]
for column, (name, dbn) in zip(st.columns(3), schools):
    with column:
        st.markdown(
            f'<div class="school-card"><strong>{escape(name)}</strong><span>{dbn}</span></div>',
            unsafe_allow_html=True,
        )

display_names = {dbn: name for name, dbn in schools}

st.divider()
st.subheader("What would you like to compare?")
st.write(
    "Ask questions in plain language and explore how schools compare across "
    "academics, attendance, student experience, and family experience."
)


def select_question(question: str) -> None:
    st.session_state["question"] = question


examples = [
    ("Which school has the highest attendance?", "Which school has the highest attendance?"),
    ("Compare student experience", "Compare student experience across the three schools."),
    ("Compare family experience", "Compare family experience across the three schools."),
]
st.caption("Try a question")
for column, (label, example) in zip(st.columns(3), examples):
    with column:
        st.button(label, on_click=select_question, args=(example,), width="stretch")

with st.form("school_question", border=False):
    question = st.text_input(
        "Your question", key="question",
        placeholder="Type your question here…",
    )
    submitted = st.form_submit_button("Ask", type="primary")

if submitted:
    # Keep one result, not a conversation history. Clear stale answers on failure.
    st.session_state.pop("result", None)
    if not question.strip():
        st.warning("Enter a question, or choose one of the examples above.")
    else:
        try:
            with st.spinner("Reviewing school data and preparing your answer…"):
                from nyc_school_navigator.generation import answer_question

                st.session_state["result"] = answer_question(question.strip())
        except Exception:
            # Configuration and driver errors may contain private connection details.
            st.error(
                "We couldn’t prepare an answer. Please try again. If the problem "
                "continues, check that the local model and school database are available."
            )

result = st.session_state.get("result")
if result:
    with st.container(border=True):
        st.caption("ANSWER")
        st.markdown(result["answer"])
        sources = result.get("sources", [])
        st.caption(f"Evidence · {len(sources)} sources")
        if not sources:
            st.caption("No supporting school sections were available for this question.")
        for source in sources:
            canonical_name = source.get("school_name", "School")
            display_name = display_names.get(source.get("dbn"), canonical_name)
            section = source.get("section", "").replace("_", " ").title()
            with st.expander(
                f'{source.get("label", "")} {display_name} · {section} · {source["score"]:.3f}',
                expanded=False,
            ):
                st.text(canonical_name)
                st.caption(
                    f'{source.get("dbn", "")} · {section} · '
                    f'{source.get("source_year", "")} · Retrieval score {source["score"]:.3f}'
                )
                st.caption("Retrieved evidence")
                evidence_text = source.get("evidence_text")
                if not evidence_text:
                    st.caption("Evidence text unavailable.")
                else:
                    st.text(evidence_text)
else:
    st.caption("Your answer and supporting school data will appear here.")

st.divider()
st.caption(
    "This prototype currently covers School Quality Report data for three schools. "
    "It does not yet include admissions rules, programs, deadlines, or live school information."
)
