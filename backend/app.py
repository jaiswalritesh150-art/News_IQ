from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

app = FastAPI()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

class NewsRequest(BaseModel):
    text: str


@app.get("/")
def home():
    return {
        "message": "NewsIQ Backend Running 🚀"
    }


@app.post("/summarize")
def summarize(news: NewsRequest):

    prompt = f"""
    Summarize the following news article in simple English.
    Keep it under 120 words.

    News:
    {news.text}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        "summary": response.text
    }