# backend/main.py
from fastapi import FastAPI, UploadFile, File
from utils.file_parser import parse_portfolio
from utils.analyzer import analyze_portfolio
from fastapi import HTTPException
from utils.news_rag import NewsRAGEngine
import requests

app = FastAPI()

OLLAMA_URL = "http://localhost:11434/api/generate"

# Initialize News RAG Engine
news_engine = NewsRAGEngine('data/news_data.json')

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
    return {"message": "Investor Portfolio Assistant API is running!"}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    try:
        portfolio_data = parse_portfolio(file.filename, content)
        analysis = analyze_portfolio(portfolio_data)
        return {"analysis": analysis}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@app.post("/ask-portfolio/")
async def ask_portfolio(question: str, file: UploadFile = File(...)):
    content = await file.read()
    portfolio_data = parse_portfolio(file.filename, content)
    if not portfolio_data:
        raise HTTPException(status_code=400, detail="No portfolio data found.")
    analysis = analyze_portfolio(portfolio_data)
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    context = news_impact_query(question)
    print("Context from news RAG:", context)
    if not context:
        raise HTTPException(status_code=404, detail="No relevant context found.")
    prompt = f"""You are an expert financial analyst. Given the context and the question, provide a detailed answer.
    portfolio_analysis = {analysis}
    Context: {context}
    Question: {question}
    Answer the question based on the context provided and also search the local news.
"""
    response = ask_ollama(prompt)
    return {"answer": response}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)
