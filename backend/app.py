from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise Exception("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NewsRequest(BaseModel):
    title: str
    description: str


@app.get("/")
def home():
    return {"message": "NewsIQ Backend Running 🚀"}


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
            model="gemini-3.5-flash",
            contents=prompt,
        )

        return {
            "summary": response.text
        }

    except Exception as e:
        return {
            "summary": f"Error: {str(e)}"
        }