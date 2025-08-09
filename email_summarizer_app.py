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
EMAILS_CSV = (
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
    """Load and cache the BART summarization pipeline."""

    return pipeline("summarization", model="facebook/bart-large-cnn")


def main() -> None:
    st.set_page_config(page_title="Email Summarizer", layout="wide")
    st.title("Email Summarizer Demo")

    if not EMAILS_CSV.exists():
        st.error(f"Email CSV not found at {EMAILS_CSV}")
        return

    emails = load_emails(EMAILS_CSV)

    options = [f"{i + 1}: {e['Sender']} ({e['SentOrRec']})" for i, e in enumerate(emails)]
    selection = st.sidebar.selectbox(
        "Select email", range(len(emails)), format_func=lambda i: options[i]
    )
    max_len = st.sidebar.slider("Max summary length", 20, 120, 60, step=5)
    email = emails[selection]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original Email")
        st.write(email["Body"])

    summarizer = get_summarizer()
    with st.spinner("Summarizing..."):
        summary = summarizer(
            email["Body"], max_length=max_len, min_length=20, do_sample=False
        )[0]["summary_text"]

    with col2:
        st.subheader("Summary")
        st.write(summary)


if __name__ == "__main__":
    main()
