from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
import os
import requests


# --------------------------------------------------
# Environment Configuration
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not configured.")

if not NEWS_API_KEY:
    raise RuntimeError("NEWS_API_KEY is not configured.")


# --------------------------------------------------
# Gemini Client
# --------------------------------------------------

client = genai.Client(api_key=GEMINI_API_KEY)


# --------------------------------------------------
# FastAPI App
# --------------------------------------------------

app = FastAPI(
    title="NewsIQ API",
    version="1.0.0",
    description="AI-powered news summarization and news discovery API"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if FRONTEND_URL == "*" else [FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Request Models
# --------------------------------------------------

class NewsRequest(BaseModel):
    title: str
    description: str


# --------------------------------------------------
# Basic Routes
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "status": "success",
        "message": "NewsIQ Backend Running 🚀"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# --------------------------------------------------
# NewsAPI - Top Headlines
# --------------------------------------------------

@app.get("/news")
def get_news(category: str = "technology"):
    url = "https://newsapi.org/v2/top-headlines"

    params = {
        "country": "us",
        "category": category,
        "apiKey": NEWS_API_KEY,
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") != "ok":
            print("NewsAPI response:", data)

            raise HTTPException(
                status_code=502,
                detail="NewsAPI returned an error."
            )

        return {
            "success": True,
            "totalResults": data.get("totalResults", 0),
            "articles": data.get("articles", [])
        }

    except requests.RequestException as e:
        print("NewsAPI error:", str(e))

        raise HTTPException(
            status_code=502,
            detail="Failed to fetch news from NewsAPI."
        )


# --------------------------------------------------
# NewsAPI - Search News
# --------------------------------------------------

@app.get("/search")
def search_news(q: str):
    if not q.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty."
        )

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": q,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWS_API_KEY,
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") != "ok":
            print("NewsAPI search response:", data)

            raise HTTPException(
                status_code=502,
                detail="NewsAPI search returned an error."
            )

        return {
            "success": True,
            "totalResults": data.get("totalResults", 0),
            "articles": data.get("articles", [])
        }

    except requests.RequestException as e:
        print("NewsAPI search error:", str(e))

        raise HTTPException(
            status_code=502,
            detail="Failed to search news from NewsAPI."
        )


# --------------------------------------------------
# AI News Summarization
# --------------------------------------------------

@app.post("/summarize")
def summarize(news: NewsRequest):
    prompt = f"""
You are an AI News Assistant.

Summarize the following news in very simple English.

Title:
{news.title}

Description:
{news.description}

Return only 5 short bullet points.
Maximum 100 words.
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )

        if not response.text:
            raise HTTPException(
                status_code=502,
                detail="Gemini returned an empty response."
            )

        return {
            "success": True,
            "summary": response.text
        }

    except HTTPException:
        raise

    except Exception as e:
        print("Gemini API error:", str(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to generate AI summary."
        )