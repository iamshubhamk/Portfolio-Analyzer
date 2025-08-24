# backend/main.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI, UploadFile, File, Form
from utils.file_parser import parse_portfolio
from utils.analyzer import analyze_portfolio
from fastapi import HTTPException
from utils.news_rag import NewsRAGEngine
import requests
import feedparser
import json
import uuid
from typing import Dict, List, Any
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

app = FastAPI()

OLLAMA_URL = "http://localhost:11434/api/generate"

def fetch_rss_news(rss_url, max_articles=30):
    feed = feedparser.parse(rss_url)
    news = []
    for entry in feed.entries[:max_articles]:
        news.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary if "summary" in entry else ""
        })
    return news

# Set BASE_DIR at the top for consistent path handling
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Instead of reading from a static file, fetch and save only the latest 30 news articles at startup
rss_url = "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
news_articles = fetch_rss_news(rss_url, max_articles=30)
news_json_path = os.path.join(BASE_DIR, "data", "news_articles.json")
os.makedirs(os.path.dirname(news_json_path), exist_ok=True)
with open(news_json_path, "w", encoding="utf-8") as f:
    json.dump(news_articles, f, ensure_ascii=False, indent=2)
news_engine = NewsRAGEngine(news_json_path)

# Simple in-memory session store
sessions: Dict[str, Dict[str, Any]] = {}

# Mount static directory at /ui instead of root
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
if not os.path.exists(PUBLIC_DIR):
    os.makedirs(PUBLIC_DIR, exist_ok=True)
app.mount("/ui", StaticFiles(directory=PUBLIC_DIR, html=True), name="static")


def news_impact_query(query: str):
    relevant_news = news_engine.search_relevant_news(query)
    return {"relevant_news": relevant_news}


def ask_ollama(prompt):
    resp = requests.post(OLLAMA_URL, json={
        "model": "phi3:mini",
        "prompt": prompt,
        "stream": False
    })
    return resp.json().get("response", "")


@app.get("/")
def read_root():
    """Redirect root to the UI"""
    return RedirectResponse(url="/ui")


@app.get("/api/health")
def health_check():
    return {"message": "Investor Portfolio Assistant API is running!"}


# Session management
@app.post("/chat/session")
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "history": [],           # list of {role, content}
        "portfolio": None        # parsed portfolio data
    }
    return {"session_id": session_id}


# Fix ValueError exception parenthesis
@app.post("/chat/upload")
async def upload_portfolio(session_id: str = Form(...), file: UploadFile = File(...)):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session_id")
    content = await file.read()
    try:
        portfolio_data = parse_portfolio(file.filename, content)
        sessions[session_id]["portfolio"] = portfolio_data
        return {"message": "Portfolio uploaded", "session_id": session_id}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@app.post("/chat/ask")
async def chat_ask(session_id: str = Form(...), question: str = Form(...)):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session_id")
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    session = sessions[session_id]
    portfolio_data = session.get("portfolio")
    if not portfolio_data:
        raise HTTPException(status_code=400, detail="Upload a portfolio first for this session.")

    # Analyze portfolio fresh each time for simplicity
    analysis = analyze_portfolio(portfolio_data)

    # Get RAG context from news
    context = news_impact_query(question)
    if not context:
        raise HTTPException(status_code=404, detail="No relevant context found.")

    # Build prompt with history for context
    chat_history_text = "\n".join([f"{turn['role'].capitalize()}: {turn['content']}" for turn in session["history"]])
    prompt = f"""You are an expert financial analyst. Use the conversation so far, the portfolio analysis, and the news context to answer the user's question.
Conversation so far:
{chat_history_text}

Portfolio analysis:
{analysis}

News context (list of dicts with title/link/summary):
{context}

User question: {question}
Provide a clear, helpful, portfolio-aware answer. If context is insufficient, say what more you need."""

    answer = ask_ollama(prompt)

    # Save to history
    session["history"].append({"role": "user", "content": question})
    session["history"].append({"role": "assistant", "content": answer})

    return {"answer": answer, "history": session["history"]}


@app.get("/chat/history/{session_id}")
def get_history(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session_id")
    return {"history": sessions[session_id]["history"]}


@app.get("/search-news/")
async def search_news(query: str, top_k: int = 5, threshold: float = 2.0):
    """
    Search for relevant news articles based on a query.
    
    Args:
        query (str): The search query
        top_k (int): Number of top results to return (default: 5)
        threshold (float): Distance threshold for relevance (default: 2.0)
    
    Returns:
        dict: Dictionary containing the relevant news articles
    """
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    try:
        results = news_engine.search_relevant_news(query, top_k=top_k, threshold=threshold)
        return {
            "query": query,
            "results_count": len(results),
            "news_articles": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching news: {str(e)}")


@app.get("/search-news/company/{company_name}")
async def search_news_by_company(company_name: str, top_k: int = 5):
    """
    Search for news articles related to a specific company.
    
    Args:
        company_name (str): Name of the company to search for
        top_k (int): Number of top results to return (default: 5)
    
    Returns:
        dict: Dictionary containing the relevant news articles
    """
    try:
        results = news_engine.search_by_company(company_name, top_k=top_k)
        return {
            "company": company_name,
            "results_count": len(results),
            "news_articles": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching news: {str(e)}")


@app.get("/search-news/topic/{topic}")
async def search_news_by_topic(topic: str, top_k: int = 5):
    """
    Search for news articles related to a specific topic.
    
    Args:
        topic (str): Topic to search for (e.g., 'market', 'earnings', 'dividend')
        top_k (int): Number of top results to return (default: 5)
    
    Returns:
        dict: Dictionary containing the relevant news articles
    """
    try:
        results = news_engine.search_by_topic(topic, top_k=top_k)
        return {
            "topic": topic,
            "results_count": len(results),
            "news_articles": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching news: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)
