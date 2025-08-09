from pathlib import Path
import csv
import streamlit as st
from transformers import pipeline

RagEmailsCsv_dir = Path('RAG-based Worm') / 'RAG Emails' / 'Emails.csv'

@st.cache_data
def load_emails(path: Path):
    emails = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['Body'] = row['Body'].strip()
            emails.append(row)
    return emails

@st.cache_resource
def get_summarizer():
    return pipeline('summarization', model='facebook/bart-large-cnn')


def main():
    st.set_page_config(page_title='Email Summarizer', layout='wide')
    st.title('Email Summarizer Demo')

    emails = load_emails(RagEmailsCsv_dir)

    options = [f"{i + 1}: {e['Sender']} ({e['SentOrRec']})" for i, e in enumerate(emails)]
    selection = st.sidebar.selectbox('Select email', range(len(emails)), format_func=lambda i: options[i])
    email = emails[selection]

    st.subheader('Original Email')
    st.write(email['Body'])

    summarizer = get_summarizer()
    with st.spinner('Summarizing...'):
        summary = summarizer(email['Body'], max_length=60, min_length=20, do_sample=False)[0]['summary_text']

    st.subheader('Summary')
    st.write(summary)


if __name__ == '__main__':
    main()
