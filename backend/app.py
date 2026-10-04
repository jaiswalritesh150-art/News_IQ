from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
import os
import requests
import time


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
# AI Summary Cache
# --------------------------------------------------

# Stores generated summaries in memory.
# Cache survives normal requests but resets when
# the backend process/server restarts.

SUMMARY_CACHE = {}

# Keep summaries cached for 6 hours.
SUMMARY_CACHE_TTL = 60 * 60 * 6


def get_cache_key(title: str, description: str) -> str:
    """
    Create a unique cache key for an article.
    """

    return f"{title.strip()}::{description.strip()}"


def get_cached_summary(
    title: str,
    description: str
):
    """
    Return cached summary if it exists
    and has not expired.
    """

    key = get_cache_key(
        title,
        description
    )

    cached = SUMMARY_CACHE.get(key)

    if not cached:
        return None

    cached_time = cached["timestamp"]

    # Remove expired cache entry
    if time.time() - cached_time > SUMMARY_CACHE_TTL:

        del SUMMARY_CACHE[key]

        return None

    return cached["summary"]


def save_cached_summary(
    title: str,
    description: str,
    summary: str
):
    """
    Save generated summary in memory.
    """

    key = get_cache_key(
        title,
        description
    )

    SUMMARY_CACHE[key] = {
        "summary": summary,
        "timestamp": time.time(),
    }


# --------------------------------------------------
# FastAPI App
# --------------------------------------------------

app = FastAPI(
    title="NewsIQ API",
    version="1.0.0",
    description=(
        "AI-powered news summarization "
        "and news discovery API"
    )
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "*"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["*"]
        if FRONTEND_URL == "*"
        else [FRONTEND_URL]
    ),
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


class BatchNewsRequest(BaseModel):
    articles: list[NewsRequest]


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
def get_news(
    category: str = "technology"
):

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

            print(
                "NewsAPI response:",
                data
            )

            raise HTTPException(
                status_code=502,
                detail="NewsAPI returned an error."
            )

        return {
            "success": True,
            "totalResults": data.get(
                "totalResults",
                0
            ),
            "articles": data.get(
                "articles",
                []
            )
        }

    except requests.RequestException as e:

        print(
            "NewsAPI error:",
            str(e)
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Failed to fetch news "
                "from NewsAPI."
            )
        )


# --------------------------------------------------
# NewsAPI - Search News
# --------------------------------------------------

@app.get("/search")
def search_news(q: str):

    if not q.strip():

        raise HTTPException(
            status_code=400,
            detail=(
                "Search query cannot be empty."
            )
        )

    url = (
        "https://newsapi.org/v2/everything"
    )

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

            print(
                "NewsAPI search response:",
                data
            )

            raise HTTPException(
                status_code=502,
                detail=(
                    "NewsAPI search returned "
                    "an error."
                )
            )

        return {
            "success": True,
            "totalResults": data.get(
                "totalResults",
                0
            ),
            "articles": data.get(
                "articles",
                []
            )
        }

    except requests.RequestException as e:

        print(
            "NewsAPI search error:",
            str(e)
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Failed to search news "
                "from NewsAPI."
            )
        )


# --------------------------------------------------
# AI - Batch News Summarization
# --------------------------------------------------

@app.post("/summarize-batch")
def summarize_batch(
    news: BatchNewsRequest
):

    # --------------------------------------------------
    # Validate Request
    # --------------------------------------------------

    if not news.articles:

        raise HTTPException(
            status_code=400,
            detail="No articles provided."
        )


    # --------------------------------------------------
    # Limit Batch Size
    # --------------------------------------------------

    articles = news.articles[:5]


    # --------------------------------------------------
    # Summary Tracking
    # --------------------------------------------------

    summaries = []

    articles_needing_ai = []


    # --------------------------------------------------
    # Check Cache
    # --------------------------------------------------

    for index, article in enumerate(
        articles
    ):

        cached_summary = get_cached_summary(
            article.title,
            article.description or ""
        )


        # ----------------------------------------------
        # Cached Article
        # ----------------------------------------------

        if cached_summary:

            summaries.append({
                "index": index,
                "summary": cached_summary,
                "cached": True
            })


        # ----------------------------------------------
        # New Article
        # ----------------------------------------------

        else:

            summaries.append({
                "index": index,
                "summary": None,
                "cached": False
            })

            articles_needing_ai.append(
                (index, article)
            )


    # --------------------------------------------------
    # If Everything Is Cached
    # --------------------------------------------------

    if not articles_needing_ai:

        print(
            "All summaries served from cache."
        )

        return {
            "success": True,
            "summaries": [
                item["summary"]
                for item in summaries
            ],
            "cached": True
        }


    # --------------------------------------------------
    # Prepare Articles for Gemini
    # --------------------------------------------------

    articles_text = ""

    for position, (
        original_index,
        article
    ) in enumerate(
        articles_needing_ai,
        start=1
    ):

        articles_text += f"""
ARTICLE {position}

Title:
{article.title}

Description:
{article.description or "No description available."}

-------------------------
"""


    # --------------------------------------------------
    # Gemini Prompt
    # --------------------------------------------------

    prompt = f"""
You are NewsIQ, an AI news assistant.

Summarize each news article below in very simple English.

{articles_text}

IMPORTANT RULES:

1. Return exactly one summary for every article.
2. Each summary must contain exactly 3 short bullet points.
3. Focus only on important facts.
4. Do not add information that is not present.
5. Do not mix information between articles.
6. Keep the language simple and easy to understand.
7. Do not write an introduction or conclusion.
8. Use exactly this format:

ARTICLE 1
- Point 1
- Point 2
- Point 3

ARTICLE 2
- Point 1
- Point 2
- Point 3

Continue the same format for every article.
"""


    # --------------------------------------------------
    # Gemini Request
    # --------------------------------------------------

    try:

        print(
            f"Sending {len(articles_needing_ai)} "
            "new articles to Gemini..."
        )

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )


        # --------------------------------------------------
        # Validate Gemini Response
        # --------------------------------------------------

        if not response.text:

            raise HTTPException(
                status_code=502,
                detail=(
                    "Gemini returned "
                    "an empty response."
                )
            )


        raw_summary = response.text.strip()

        print(
            "Gemini response received."
        )


        # --------------------------------------------------
        # Parse Gemini Response
        # --------------------------------------------------

        generated_summaries = []


        for position in range(
            1,
            len(articles_needing_ai) + 1
        ):

            marker = (
                f"ARTICLE {position}"
            )

            start = raw_summary.find(
                marker
            )


            if start == -1:

                generated_summaries.append(
                    "Summary unavailable."
                )

                continue


            start += len(marker)


            next_marker = (
                f"ARTICLE {position + 1}"
            )


            end = raw_summary.find(
                next_marker,
                start
            )


            if end == -1:

                section = (
                    raw_summary[start:]
                )

            else:

                section = (
                    raw_summary[start:end]
                )


            section = section.strip()


            if not section:

                section = (
                    "Summary unavailable."
                )


            generated_summaries.append(
                section
            )


        # --------------------------------------------------
        # Save Generated Summaries
        # --------------------------------------------------

        for generated_index, (
            original_index,
            article
        ) in enumerate(
            articles_needing_ai
        ):

            if (
                generated_index
                < len(generated_summaries)
            ):

                generated_summary = (
                    generated_summaries[
                        generated_index
                    ]
                )

            else:

                generated_summary = (
                    "Summary unavailable."
                )


            # ----------------------------------------------
            # Update Result
            # ----------------------------------------------

            summaries[
                original_index
            ]["summary"] = generated_summary


            # ----------------------------------------------
            # Save to Cache
            # ----------------------------------------------

            if (
                generated_summary
                != "Summary unavailable."
            ):

                save_cached_summary(
                    article.title,
                    article.description or "",
                    generated_summary
                )


        # --------------------------------------------------
        # Final Response
        # --------------------------------------------------

        return {
            "success": True,
            "summaries": [
                item["summary"]
                or "Summary unavailable."
                for item in summaries
            ],
            "cached": False
        }


    # --------------------------------------------------
    # HTTP Exceptions
    # --------------------------------------------------

    except HTTPException:

        raise


    # --------------------------------------------------
    # Gemini Errors
    # --------------------------------------------------

    except Exception as e:

        error_text = str(e)

        print(
            "Gemini batch API error:",
            repr(e)
        )


        # --------------------------------------------------
        # Rate Limit / Quota Error
        # --------------------------------------------------

        if (
            "429" in error_text
            or
            "RESOURCE_EXHAUSTED"
            in error_text
            or
            "quota"
            in error_text.lower()
        ):

            raise HTTPException(
                status_code=429,
                detail=(
                    "AI summary quota is "
                    "temporarily unavailable. "
                    "Please try again later."
                )
            )


        # --------------------------------------------------
        # Other Gemini Errors
        # --------------------------------------------------

        raise HTTPException(
            status_code=502,
            detail=(
                "AI summary service is "
                "temporarily unavailable."
            )
        )