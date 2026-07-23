from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
import os

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise Exception("GEMINI_API_KEY not found.")

# Gemini Client
client = genai.Client(api_key=API_KEY)

# FastAPI App
app = FastAPI(
    title="NewsIQ API",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Change to your Vercel URL after deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Model
class NewsRequest(BaseModel):
    title: str
    description: str

# Health Check
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

# Summarize News
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
            model="gemini-2.5-flash",
            contents=prompt,
        )

        return {
            "success": True,
            "summary": response.text
        }

    except Exception as e:
        return {
            "success": False,
            "summary": "",
            "error": str(e)
        }