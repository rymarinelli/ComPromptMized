"""Streamlit demo that summarizes emails from a CSV file using an open-source
BART model.

The demo loads emails from ``RAG-based Worm/RAG Emails/Emails.csv`` and lets the
user pick one to summarize. A slider controls the maximum length of the
generated summary.
"""

from pathlib import Path
import csv
import streamlit as st
from transformers import pipeline


# Path to the bundled CSV with example emails
RagEmailsCsv_dir = (
    Path(__file__).parent / "RAG-based Worm" / "RAG Emails" / "Emails.csv"
)


@st.cache_data
def load_emails(path: Path):
    """Return a list of emails from ``path``."""

    emails = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["Body"] = row["Body"].strip()
            emails.append(row)
    return emails


@st.cache_resource
def get_summarizer():
    """Load and cache the BART summarization pipeline.

    If the model or its dependencies are missing, display an error and
    return ``None`` so the rest of the app can continue to run.
    """

    try:
        return pipeline("summarization", model="facebook/bart-large-cnn")
    except Exception as exc:  # pragma: no cover - protective fallback
        st.error(
            "Could not load the summarization model."
            " Ensure `torch` and `transformers` are installed."
        )
        st.exception(exc)
        return None


def render_email(email: dict) -> None:
    """Display an email in a styled container."""
    st.markdown(
        f"""
        <div class='email-card'>
            <div><strong>From:</strong> {email['Sender']} <em>({email['SentOrRec']})</em></div>
            <div style='margin-top:0.5rem; white-space:pre-wrap;'>{email['Body']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary(text: str) -> None:
    """Display a summary in a styled container."""
    st.markdown(
        f"""
        <div class='summary-card'>{text}</div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Email Summarizer", page_icon="📧", layout="wide")
    st.markdown(
        """
        <style>
        .email-card, .summary-card {
            padding:1rem;
            border:1px solid var(--secondary-background-color);
            border-radius:0.5rem;
            background-color:var(--background-color);
            color:var(--text-color);
        }
        .summary-card {
            background-color:var(--secondary-background-color);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("Email Summarizer Demo")

    if not RagEmailsCsv_dir.exists():
        st.error(f"Email CSV not found at {RagEmailsCsv_dir}")
        return

    emails = load_emails(RagEmailsCsv_dir)

    options = [f"{i + 1}: {e['Sender']} ({e['SentOrRec']})" for i, e in enumerate(emails)]
    selection = st.sidebar.selectbox(
        "Select email", range(len(emails)), format_func=lambda i: options[i]
    )
    max_len = st.sidebar.slider("Max summary length", 20, 120, 60, step=5)
    email = emails[selection]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original Email")
        render_email(email)

    summarizer = get_summarizer()
    if summarizer is None:
        return

    with st.spinner("Summarizing..."):
        summary = summarizer(
            email["Body"], max_length=max_len, min_length=20, do_sample=False
        )[0]["summary_text"]

    with col2:
        st.subheader("Summary")
        render_summary(summary)


if __name__ == "__main__":
    main()
