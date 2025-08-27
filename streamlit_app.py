import streamlit as st
import requests

st.set_page_config(page_title="Portfolio Analyzer", layout="centered", initial_sidebar_state="collapsed")
st.title("📊 Investor Portfolio Assistant")

# Add a little padding for mobile
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        flex-wrap: wrap;
    }
    .stButton>button {
        width: 100%;
    }
    .stFileUploader {
        width: 100% !important;
    }
    @media (max-width: 600px) {
        .stTabs [data-baseweb="tab-list"] {
            flex-direction: column;
        }
        .stTextInput>div>input, .stNumberInput>div>input {
            width: 100% !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Backend URL (adjust if running on a different port or host)
BACKEND_URL = "https://portfolio-analyzer-backend-4f9z.onrender.com"

# Session state for session_id
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = None

# Move session creation to main area for visibility
st.header("Session Management")
session_col1, session_col2 = st.columns([2, 3])
with session_col1:
    if st.button("Create New Session"):
        with st.spinner("Creating session..."):
            resp = requests.post(f"{BACKEND_URL}/chat/session")
        if resp.status_code == 200:
            st.session_state['session_id'] = resp.json()['session_id']
            st.success(f"Session created: {st.session_state['session_id']}")
        else:
            st.error("Failed to create session.")
with session_col2:
    if st.session_state['session_id']:
        st.info(f"Current Session ID: {st.session_state['session_id']}")
    else:
        st.warning("No session active. Please create a session.")

st.header("1. Upload Your Portfolio File")
portfolio_file = st.file_uploader("Choose a portfolio file (CSV, Excel, PDF)", type=["csv", "xlsx", "pdf"])

if st.session_state['session_id'] and portfolio_file is not None:
    upload_placeholder = st.empty()
    if upload_placeholder.button("Upload Portfolio File"):
        with st.spinner("Uploading portfolio file..."):
            files = {"file": (portfolio_file.name, portfolio_file.getvalue())}
            data = {"session_id": st.session_state['session_id']}
            upload_url = f"{BACKEND_URL}/chat/upload"
            resp = requests.post(upload_url, data=data, files=files)
        if resp.status_code == 200:
            st.success("Portfolio uploaded successfully!")
        else:
            st.error(f"Failed to upload portfolio: {resp.json().get('detail', resp.text)}")

st.header("2. Ask Questions About Your Portfolio")
if st.session_state['session_id']:
    question = st.text_input("Enter your question about your portfolio:")
    ask_placeholder = st.empty()
    if ask_placeholder.button("Ask Question") and question.strip():
        with st.spinner("Getting answer from assistant..."):
            ask_url = f"{BACKEND_URL}/chat/ask"
            data = {"session_id": st.session_state['session_id'], "question": question}
            resp = requests.post(ask_url, data=data)
        if resp.status_code == 200:
            answer = resp.json().get("answer", "No answer returned.")
            st.success(f"Assistant: {answer}")
            # Optionally show chat history
            history = resp.json().get("history", [])
            with st.expander("Show Chat History"):
                for turn in history:
                    st.markdown(f"**{turn['role'].capitalize()}:** {turn['content']}")
        else:
            st.error(f"Failed to get answer: {resp.json().get('detail', resp.text)}")

st.header("3. Search Relevant News")
news_tab = st.tabs(["By Query", "By Company", "By Topic"])

with news_tab[0]:
    st.subheader("Search News by Query")
    news_query = st.text_input("Enter a search query for news articles:", key="news_query")
    top_k = st.number_input("Number of results", min_value=1, max_value=20, value=5, key="news_topk")
    news_query_placeholder = st.empty()
    if news_query_placeholder.button("Search News", key="search_news_btn") and news_query.strip():
        with st.spinner("Searching news articles..."):
            url = f"{BACKEND_URL}/search-news/"
            params = {"query": news_query, "top_k": top_k}
            resp = requests.get(url, params=params)
        if resp.status_code == 200:
            articles = resp.json().get("news_articles", [])
            st.write(f"Found {len(articles)} articles:")
            for art in articles:
                st.markdown(f"- [{art['title']}]({art['link']})\n  {art.get('summary', '')}")
        else:
            st.error(f"Error: {resp.json().get('detail', resp.text)}")

with news_tab[1]:
    st.subheader("Search News by Company")
    company = st.text_input("Enter company name:", key="company_name")
    top_k_c = st.number_input("Number of results", min_value=1, max_value=20, value=5, key="company_topk")
    company_query_placeholder = st.empty()
    if company_query_placeholder.button("Search by Company", key="search_company_btn") and company.strip():
        with st.spinner("Searching company news..."):
            url = f"{BACKEND_URL}/search-news/company/{company}"
            params = {"top_k": top_k_c}
            resp = requests.get(url, params=params)
        if resp.status_code == 200:
            articles = resp.json().get("news_articles", [])
            st.write(f"Found {len(articles)} articles:")
            for art in articles:
                st.markdown(f"- [{art['title']}]({art['link']})\n  {art.get('summary', '')}")
        else:
            st.error(f"Error: {resp.json().get('detail', resp.text)}")

with news_tab[2]:
    st.subheader("Search News by Topic")
    topic = st.text_input("Enter topic (e.g., market, earnings, dividend):", key="topic_name")
    top_k_t = st.number_input("Number of results", min_value=1, max_value=20, value=5, key="topic_topk")
    topic_query_placeholder = st.empty()
    if topic_query_placeholder.button("Search by Topic", key="search_topic_btn") and topic.strip():
        with st.spinner("Searching topic news..."):
            url = f"{BACKEND_URL}/search-news/topic/{topic}"
            params = {"top_k": top_k_t}
            resp = requests.get(url, params=params)
        if resp.status_code == 200:
            articles = resp.json().get("news_articles", [])
            st.write(f"Found {len(articles)} articles:")
            for art in articles:
                st.markdown(f"- [{art['title']}]({art['link']})\n  {art.get('summary', '')}")
        else:
            st.error(f"Error: {resp.json().get('detail', resp.text)}")