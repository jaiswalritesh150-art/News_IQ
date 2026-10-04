from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
import os

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not configured.")

# Gemini Client
client = genai.Client(api_key=API_KEY)

# FastAPI App
app = FastAPI(
    title="NewsIQ API",
    version="1.0.0",
    description="AI-powered news summarization API"
)

# CORS
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if FRONTEND_URL == "*" else [FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NewsRequest(BaseModel):
    title: str
    description: str


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
