from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from groq import Groq

from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
from models import Article, Summary

import os
import re
import requests
import time
from datetime import datetime


# ============================================================
# Environment Configuration
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")


if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not configured.")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not configured.")

if not NEWS_API_KEY:
    raise RuntimeError("NEWS_API_KEY is not configured.")


# ============================================================
# AI Clients
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=genai.types.HttpOptions(
        timeout=10000
    )
)

groq_client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# Database Initialization
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# AI Summary Cache
# ============================================================

SUMMARY_CACHE = {}

SUMMARY_CACHE_TTL = 60 * 60 * 6


def get_cache_key(
    title: str,
    description: str,
    language: str = "English"
) -> str:

    return (
        f"{language.strip()}::"
        f"{title.strip()}::"
        f"{description.strip()}"
    )


def get_cached_summary(
    title: str,
    description: str,
    language: str = "English"
):

    key = get_cache_key(
        title,
        description,
        language
    )

    cached = SUMMARY_CACHE.get(key)

    if not cached:
        return None

    cached_time = cached["timestamp"]

    if time.time() - cached_time > SUMMARY_CACHE_TTL:

        del SUMMARY_CACHE[key]

        return None

    return cached["summary"]


def save_cached_summary(
    title: str,
    description: str,
    summary: str,
    language: str = "English"
):

    key = get_cache_key(
        title,
        description,
        language
    )

    SUMMARY_CACHE[key] = {
        "summary": summary,
        "timestamp": time.time(),
    }


# ============================================================
# Database Helpers
# ============================================================

def parse_published_at(value):
    """
    Convert NewsAPI publishedAt string into datetime.
    Returns None if parsing fails.
    """

    if not value:
        return None

    if isinstance(value, datetime):
        return value

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).replace(tzinfo=None)

    except (ValueError, TypeError):
        return None


def save_article_to_db(
    article_data: dict,
    db: Session
):
    """
    Create or update an article using URL as the unique key.
    """

    url = article_data.get("url")

    if not url:
        return None

    existing_article = db.scalar(
        select(Article).where(
            Article.url == url
        )
    )

    published_at = parse_published_at(
        article_data.get("publishedAt")
    )

    if existing_article:

        existing_article.title = (
            article_data.get("title")
            or existing_article.title
        )

        existing_article.description = (
            article_data.get("description")
        )

        existing_article.source = (
            article_data.get("source", {}).get("name")
            if isinstance(
                article_data.get("source"),
                dict
            )
            else article_data.get("source")
        )

        existing_article.image_url = (
            article_data.get("urlToImage")
            or existing_article.image_url
        )

        existing_article.category = (
            article_data.get("category")
            or existing_article.category
        )

        if published_at:
            existing_article.published_at = published_at

        db.commit()
        db.refresh(existing_article)

        return existing_article

    source_name = (
        article_data.get("source", {}).get("name")
        if isinstance(
            article_data.get("source"),
            dict
        )
        else article_data.get("source")
    )

    new_article = Article(
        title=article_data.get("title")
        or "Untitled Article",

        description=article_data.get(
            "description"
        ),

        source=source_name,

        url=url,

        image_url=article_data.get(
            "urlToImage"
        ),

        category=article_data.get(
            "category"
        ),

        published_at=published_at,
    )

    db.add(new_article)

    db.commit()
    db.refresh(new_article)

    return new_article


def save_articles_to_db(
    articles: list,
    category: str | None = None
):
    """
    Save a list of NewsAPI articles.
    """

    if not articles:
        return

    db = SessionLocal()

    try:

        saved_count = 0

        for article in articles:

            article_copy = dict(article)

            if category:
                article_copy["category"] = category

            saved_article = save_article_to_db(
                article_copy,
                db
            )

            if saved_article:
                saved_count += 1

        print(
            f"Database: saved/updated "
            f"{saved_count} articles."
        )

    except Exception as e:

        db.rollback()

        print(
            "Database article save error:",
            repr(e)
        )

    finally:

        db.close()


def save_summary_to_db(
    article,
    summary_text: str,
    language: str
):
    """
    Save a generated summary for an existing article.

    Prevents duplicate summary rows for the
    same article + language.
    """

    if not article:
        return

    if not summary_text:
        return

    if summary_text == "Summary unavailable.":
        return

    db = SessionLocal()

    try:

        db_article = db.scalar(
            select(Article).where(
                Article.url == article.url
            )
        )

        if not db_article:
            return

        existing_summary = db.scalar(
            select(Summary).where(
                Summary.article_id == db_article.id,
                Summary.language == language
            )
        )

        if existing_summary:

            existing_summary.summary = summary_text

        else:

            new_summary = Summary(
                article_id=db_article.id,
                summary=summary_text,
                language=language,
            )

            db.add(new_summary)

        db.commit()

        print(
            "Database: summary saved for:",
            db_article.title
        )

    except Exception as e:

        db.rollback()

        print(
            "Database summary save error:",
            repr(e)
        )

    finally:

        db.close()


# ============================================================
# FastAPI App
# ============================================================

app = FastAPI(
    title="NewsIQ API",
    version="1.0.0",
    description=(
        "AI-powered news summarization "
        "and news discovery API"
    )
)


# ============================================================
# CORS
# ============================================================

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


# ============================================================
# Request Models
# ============================================================

class NewsRequest(BaseModel):
    title: str
    description: str

    # Optional article metadata.
    # Frontend will send these after the next update.
    url: str | None = None
    source: str | None = None
    image_url: str | None = None
    category: str | None = None
    published_at: str | None = None


class BatchNewsRequest(BaseModel):
    articles: list[NewsRequest]
    language: str = "English"


# ============================================================
# Basic Routes
# ============================================================

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


# ============================================================
# NewsAPI - Top Headlines
# ============================================================

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

        articles = data.get(
            "articles",
            []
        )

        # ----------------------------------------------------
        # Save NewsAPI articles to PostgreSQL
        # ----------------------------------------------------

        save_articles_to_db(
            articles,
            category=category
        )

        return {
            "success": True,
            "totalResults": data.get(
                "totalResults",
                0
            ),
            "articles": articles
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


# ============================================================
# NewsAPI - Search News
# ============================================================

@app.get("/search")
def search_news(q: str):

    if not q.strip():

        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty."
        )


    # --------------------------------------------------------
    # Normalize Search Query
    # --------------------------------------------------------

    search_query = q.strip()

    search_query = re.sub(
        r"\bmens\b",
        "men's",
        search_query,
        flags=re.IGNORECASE
    )

    search_query = re.sub(
        r"\bwomens\b",
        "women's",
        search_query,
        flags=re.IGNORECASE
    )

    search_query = re.sub(
        r"\s+",
        " ",
        search_query
    ).strip()


    # --------------------------------------------------------
    # NewsAPI Request
    # --------------------------------------------------------

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": search_query,
        "sortBy": "relevancy",
        "language": "en",
        "pageSize": 20,
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

        articles = data.get(
            "articles",
            []
        )


        # ----------------------------------------------------
        # Relevance Filtering
        # ----------------------------------------------------

        query_words = [
            word.lower().strip(
                ".,!?;:\"'()[]{}"
            )
            for word in search_query.split()
            if len(
                word.strip(
                    ".,!?;:\"'()[]{}"
                )
            ) > 2
        ]

        relevant_articles = []

        for article in articles:

            title = (
                article.get("title")
                or ""
            ).lower()

            description = (
                article.get("description")
                or ""
            ).lower()

            content = (
                f"{title} {description}"
            )

            matched_words = 0

            for word in query_words:

                if word in content:

                    matched_words += 1
                    continue

                normalized_word = word.replace(
                    "'",
                    ""
                )

                normalized_content = content.replace(
                    "'",
                    ""
                )

                if normalized_word in normalized_content:

                    matched_words += 1


            required_matches = max(
                1,
                (len(query_words) + 1) // 2
            )

            if matched_words >= required_matches:

                relevant_articles.append(
                    article
                )


        # ----------------------------------------------------
        # Save Search Results to PostgreSQL
        # ----------------------------------------------------

        save_articles_to_db(
            relevant_articles
        )


        return {
            "success": True,
            "totalResults": len(
                relevant_articles
            ),
            "articles": relevant_articles
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


# ============================================================
# AI - Batch News Summarization
# ============================================================

@app.post("/summarize-batch")
def summarize_batch(
    news: BatchNewsRequest
):

    if not news.articles:

        raise HTTPException(
            status_code=400,
            detail="No articles provided."
        )


    # --------------------------------------------------------
    # Limit Batch Size
    # --------------------------------------------------------

    articles = news.articles[:5]


    # --------------------------------------------------------
    # Summary Tracking
    # --------------------------------------------------------

    summaries = []
    articles_needing_ai = []


    # --------------------------------------------------------
    # Check Cache
    # --------------------------------------------------------

    for index, article in enumerate(articles):

        cached_summary = get_cached_summary(
            article.title,
            article.description or "",
            news.language
        )

        if cached_summary:

            summaries.append({
                "index": index,
                "summary": cached_summary,
                "cached": True
            })

        else:

            summaries.append({
                "index": index,
                "summary": None,
                "cached": False
            })

            articles_needing_ai.append(
                (index, article)
            )


    # --------------------------------------------------------
    # Everything Cached
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Prepare Articles
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # AI Prompt
    # --------------------------------------------------------

    prompt = f"""
You are NewsIQ, an AI news assistant.

Summarize each news article below in very simple language.

The requested output language is: {news.language}

Write the complete summary in the requested language.

{articles_text}

IMPORTANT RULES:

1. Return exactly one summary for every article.
2. Each summary must contain exactly 5 short bullet points.
3. Each bullet should contain useful and different information.
4. Cover the main event, important facts, people or organizations involved, impact, and what happens next when available.
5. Do not repeat the same information in different bullets.
6. Do not add information that is not present in the article.
7. Do not mix information between articles.
8. Keep the language simple and easy to understand.
9. Each bullet should normally be 1-2 short sentences.
10. Use natural and easy-to-understand language for the selected language.
11. Do not translate names of people, organizations, places, or official terms unless it is natural to do so.
12. Do not change the meaning of the original article.
13. Do not write an introduction or conclusion.
14. Use exactly this format:

ARTICLE 1
- Point 1
- Point 2
- Point 3
- Point 4
- Point 5

ARTICLE 2
- Point 1
- Point 2
- Point 3
- Point 4
- Point 5

Continue the same format for every article.
"""


    # ========================================================
    # Generate AI Summary
    # ========================================================

    try:

        raw_summary = None


        # ====================================================
        # GEMINI PRIMARY
        # ====================================================

        try:

            print(
                f"Sending {len(articles_needing_ai)} "
                "new articles to Gemini..."
            )

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )

            if response and response.text:

                raw_summary = response.text.strip()

                print(
                    "Gemini response received."
                )

            else:

                raise RuntimeError(
                    "Gemini returned empty content."
                )


        except Exception as gemini_error:

            gemini_error_text = str(
                gemini_error
            )

            print(
                "Gemini failed:",
                repr(gemini_error)
            )


            # ------------------------------------------------
            # Gemini Quota / Availability Check
            # ------------------------------------------------

            is_fallback_error = (
                "429" in gemini_error_text
                or
                "RESOURCE_EXHAUSTED"
                in gemini_error_text
                or
                "quota"
                in gemini_error_text.lower()
                or
                "504" in gemini_error_text
                or
                "DEADLINE_EXCEEDED"
                in gemini_error_text
                or
                "503" in gemini_error_text
                or
                "UNAVAILABLE"
                in gemini_error_text
                or
                "timeout"
                in gemini_error_text.lower()
                or
                "timed out"
                in gemini_error_text.lower()
            )


            if not is_fallback_error:

                raise gemini_error


            # =================================================
            # GROQ FALLBACK
            # =================================================

            print(
                "Gemini quota exceeded."
            )

            print(
                "Falling back to Groq..."
            )


            try:

                groq_response = (
                    groq_client.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.2,
                    )
                )


                print(
                    "Groq response type:",
                    type(groq_response)
                )

                print(
                    "Groq choices count:",
                    len(groq_response.choices)
                    if groq_response
                    and groq_response.choices
                    else 0
                )


                if (
                    not groq_response
                    or not groq_response.choices
                ):

                    raise RuntimeError(
                        "Groq returned no choices."
                    )


                choice = (
                    groq_response
                    .choices[0]
                )


                if not choice:

                    raise RuntimeError(
                        "Groq returned an empty choice."
                    )


                message = choice.message


                if not message:

                    raise RuntimeError(
                        "Groq returned no message."
                    )


                content = getattr(
                    message,
                    "content",
                    None
                )

                reasoning = getattr(
                    message,
                    "reasoning",
                    None
                )


                print(
                    "Groq content exists:",
                    bool(content)
                )

                print(
                    "Groq reasoning exists:",
                    bool(reasoning)
                )


                if content:

                    raw_summary = content.strip()

                elif reasoning:

                    raw_summary = reasoning.strip()

                else:

                    print(
                        "Groq returned no content/reasoning."
                    )

                    print(
                        "Groq FULL RESPONSE:",
                        groq_response
                    )

                    raise RuntimeError(
                        "Groq returned empty content."
                    )


                if not raw_summary:

                    raise RuntimeError(
                        "Groq returned blank text."
                    )


                print(
                    "Groq response received."
                )


            except Exception as groq_error:

                print(
                    "Groq fallback failed:",
                    repr(groq_error)
                )

                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Both Gemini and Groq "
                        "summary services are "
                        "temporarily unavailable."
                    )
                )


        # ====================================================
        # Validate AI Response
        # ====================================================

        if not raw_summary:

            raise HTTPException(
                status_code=502,
                detail=(
                    "AI returned "
                    "an empty response."
                )
            )


        # ====================================================
        # Parse AI Response
        # ====================================================

        generated_summaries = []

        cleaned_raw = re.sub(
            r"```(?:text|markdown)?",
            "",
            raw_summary,
            flags=re.IGNORECASE
        ).replace("```", "").strip()


        # ----------------------------------------------------
        # Primary parser
        # ----------------------------------------------------

        article_pattern = re.compile(
            r"ARTICLE\s+(\d+)\s*(.*?)(?=ARTICLE\s+\d+|$)",
            re.IGNORECASE | re.DOTALL
        )

        matches = article_pattern.findall(
            cleaned_raw
        )

        if matches:

            parsed_by_number = {}

            for number, section in matches:

                section = section.strip()

                section = re.sub(
                    r"^\s*(?:summary\s*:?)\s*",
                    "",
                    section,
                    flags=re.IGNORECASE
                ).strip()

                if section:

                    parsed_by_number[
                        int(number)
                    ] = section


            for position in range(
                1,
                len(articles_needing_ai) + 1
            ):

                generated_summaries.append(
                    parsed_by_number.get(
                        position,
                        "Summary unavailable."
                    )
                )

        else:

            # ------------------------------------------------
            # Fallback parser
            # ------------------------------------------------

            lines = [
                line.strip()
                for line in cleaned_raw.splitlines()
                if line.strip()
            ]


            lines = [
                line
                for line in lines
                if not re.match(
                    r"^(?:summary|article\s*\d*)\s*:?$",
                    line,
                    re.IGNORECASE
                )
            ]


            expected_count = len(
                articles_needing_ai
            )

            bullet_lines = []

            for line in lines:

                cleaned_line = re.sub(
                    r"^(?:[-?*]|\d+[.)])\s+",
                    "",
                    line
                ).strip()

                if cleaned_line:

                    bullet_lines.append(
                        cleaned_line
                    )


            if len(bullet_lines) >= expected_count * 5:

                for position in range(
                    expected_count
                ):

                    points = bullet_lines[
                        position * 5:
                        (position + 1) * 5
                    ]

                    generated_summaries.append(
                        "\n".join(
                            f"- {point}"
                            for point in points
                        )
                    )

            else:

                for position in range(
                    expected_count
                ):

                    if position < len(lines):

                        generated_summaries.append(
                            lines[position]
                        )

                    else:

                        generated_summaries.append(
                            "Summary unavailable."
                        )


        # ----------------------------------------------------
        # Guarantee one result per AI article
        # ----------------------------------------------------

        while len(
            generated_summaries
        ) < len(articles_needing_ai):

            generated_summaries.append(
                "Summary unavailable."
            )


        generated_summaries = (
            generated_summaries[
                :len(articles_needing_ai)
            ]
        )


        # ====================================================
        # Save Generated Summaries
        # ====================================================

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


            summaries[
                original_index
            ]["summary"] = generated_summary


            # ------------------------------------------------
            # Cache Summary
            # ------------------------------------------------

            if (
                generated_summary
                != "Summary unavailable."
            ):

                save_cached_summary(
                    article.title,
                    article.description or "",
                    generated_summary,
                    news.language
                )


            # ------------------------------------------------
            # Save Summary to PostgreSQL
            # ------------------------------------------------

            if (
                generated_summary
                != "Summary unavailable."
                and article.url
            ):

                try:

                    db = SessionLocal()

                    try:

                        article_data = {
                            "title": article.title,
                            "description": article.description,
                            "url": article.url,
                            "source": article.source,
                            "urlToImage": article.image_url,
                            "category": article.category,
                            "publishedAt": article.published_at,
                        }

                        db_article = save_article_to_db(
                            article_data,
                            db
                        )

                    finally:

                        db.close()


                    if db_article:

                        save_summary_to_db(
                            db_article,
                            generated_summary,
                            news.language
                        )

                except Exception as db_error:

                    print(
                        "Database summary integration error:",
                        repr(db_error)
                    )


        # ====================================================
        # Final Response
        # ====================================================

        return {
            "success": True,
            "summaries": [
                item["summary"]
                or "Summary unavailable."
                for item in summaries
            ],
            "cached": False
        }


    except HTTPException:

        raise


    except Exception as e:

        print(
            "AI batch API error:",
            repr(e)
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "AI summary service is "
                "temporarily unavailable."
            )
        )