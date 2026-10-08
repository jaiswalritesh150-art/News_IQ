from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from groq import Groq

from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
from models import Article, Summary

import os
import re
import requests
import time
from datetime import datetime


# =========================================================
# ENVIRONMENT
# =========================================================

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


# =========================================================
# AI CLIENTS
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=genai.types.HttpOptions(timeout=10000),
)

groq_client = Groq(api_key=GROQ_API_KEY)


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# IN-MEMORY SUMMARY CACHE
# =========================================================

SUMMARY_CACHE = {}
SUMMARY_CACHE_TTL = 60 * 60 * 6


def get_cache_key(
    title: str,
    description: str,
    language: str = "English",
) -> str:
    return (
        f"{language.strip()}::"
        f"{title.strip()}::"
        f"{description.strip()}"
    )


def get_cached_summary(
    title: str,
    description: str,
    language: str = "English",
):
    key = get_cache_key(title, description, language)

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
    language: str = "English",
):
    key = get_cache_key(title, description, language)

    SUMMARY_CACHE[key] = {
        "summary": summary,
        "timestamp": time.time(),
    }


# =========================================================
# HELPERS
# =========================================================

def parse_published_at(value):
    if not value:
        return None

    if isinstance(value, datetime):
        return value.replace(tzinfo=None)

    try:
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        if parsed.tzinfo:
            parsed = parsed.replace(tzinfo=None)

        return parsed

    except Exception:
        return None


def article_to_dict(article: Article):
    return {
        "id": article.id,
        "title": article.title,
        "description": article.description,
        "source": article.source,
        "url": article.url,
        "image_url": article.image_url,
        "category": article.category,
        "published_at": (
            article.published_at.isoformat()
            if article.published_at
            else None
        ),
        "created_at": (
            article.created_at.isoformat()
            if article.created_at
            else None
        ),
    }


def summary_to_dict(summary: Summary):
    return {
        "id": summary.id,
        "article_id": summary.article_id,
        "summary": summary.summary,
        "language": summary.language,
        "created_at": (
            summary.created_at.isoformat()
            if summary.created_at
            else None
        ),
    }


# =========================================================
# DATABASE ARTICLE FUNCTIONS
# =========================================================

def save_article_to_db(
    article: dict,
    category: str | None = None,
):
    url = article.get("url")

    if not url:
        return None

    title = article.get("title") or "Untitled"
    description = article.get("description")

    source_data = article.get("source") or {}
    source = (
        source_data.get("name")
        if isinstance(source_data, dict)
        else source_data
    )

    image_url = article.get("urlToImage") or article.get("image_url")

    article_category = (
        category.strip().lower()
        if category
        else article.get("category")
    )

    published_at = parse_published_at(
        article.get("publishedAt") or article.get("published_at")
    )

    db = SessionLocal()

    try:
        db_article = db.scalar(
            select(Article).where(Article.url == url)
        )

        if db_article:
            db_article.title = title
            db_article.description = description
            db_article.source = source
            db_article.image_url = image_url
            db_article.category = article_category
            db_article.published_at = published_at

        else:
            db_article = Article(
                title=title,
                description=description,
                source=source,
                url=url,
                image_url=image_url,
                category=article_category,
                published_at=published_at,
            )

            db.add(db_article)

        db.commit()
        db.refresh(db_article)

        return db_article.id

    except Exception as e:
        db.rollback()
        print("Database article save error:", repr(e))
        return None

    finally:
        db.close()


def save_articles_to_db(
    articles: list,
    category: str | None = None,
):
    if not articles:
        return

    db = SessionLocal()

    saved_count = 0

    try:
        for article in articles:
            url = article.get("url")

            if not url:
                continue

            title = article.get("title") or "Untitled"
            description = article.get("description")

            source_data = article.get("source") or {}

            source = (
                source_data.get("name")
                if isinstance(source_data, dict)
                else source_data
            )

            image_url = (
                article.get("urlToImage")
                or article.get("image_url")
            )

            article_category = (
                category.strip().lower()
                if category
                else article.get("category")
            )

            published_at = parse_published_at(
                article.get("publishedAt")
                or article.get("published_at")
            )

            db_article = db.scalar(
                select(Article).where(Article.url == url)
            )

            if db_article:
                db_article.title = title
                db_article.description = description
                db_article.source = source
                db_article.image_url = image_url
                db_article.category = article_category
                db_article.published_at = published_at

            else:
                db_article = Article(
                    title=title,
                    description=description,
                    source=source,
                    url=url,
                    image_url=image_url,
                    category=article_category,
                    published_at=published_at,
                )

                db.add(db_article)

            saved_count += 1

        db.commit()

        print(f"Saved/updated {saved_count} articles in database.")

    except Exception as e:
        db.rollback()
        print("Database bulk save error:", repr(e))

    finally:
        db.close()


# =========================================================
# DATABASE SUMMARY FUNCTIONS
# =========================================================

def save_summary_to_db(
    article_url: str,
    summary_text: str,
    language: str = "English",
):
    if not article_url or not summary_text:
        return False

    db = SessionLocal()

    try:
        article = db.scalar(
            select(Article).where(Article.url == article_url)
        )

        if not article:
            return False

        existing_summary = db.scalar(
            select(Summary)
            .where(
                Summary.article_id == article.id,
                Summary.language == language,
            )
            .order_by(Summary.created_at.desc())
        )

        if existing_summary:
            existing_summary.summary = summary_text

        else:
            db.add(
                Summary(
                    article_id=article.id,
                    summary=summary_text,
                    language=language,
                )
            )

        db.commit()

        return True

    except Exception as e:
        db.rollback()
        print("Database summary save error:", repr(e))
        return False

    finally:
        db.close()


def get_db_cached_summary(
    article_url: str,
    language: str = "English",
):
    if not article_url:
        return None

    db = SessionLocal()

    try:
        article = db.scalar(
            select(Article).where(Article.url == article_url)
        )

        if not article:
            return None

        summary = db.scalar(
            select(Summary)
            .where(
                Summary.article_id == article.id,
                Summary.language == language,
            )
            .order_by(Summary.created_at.desc())
        )

        if summary:
            return summary.summary

        return None

    except Exception as e:
        print("Database cache lookup error:", repr(e))
        return None

    finally:
        db.close()


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="NewsIQ API",
    description="AI-powered news aggregation, search, summarization and database API.",
    version="2.0.0",
)


# =========================================================
# CORS
# =========================================================

FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

if FRONTEND_URL == "*":
    allow_origins = ["*"]
    allow_credentials = False
else:
    allow_origins = [FRONTEND_URL]
    allow_credentials = True


app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# REQUEST MODELS
# =========================================================

class NewsRequest(BaseModel):
    title: str
    description: str
    url: str | None = None
    source: str | None = None
    image_url: str | None = None
    category: str | None = None
    published_at: str | None = None


class BatchNewsRequest(BaseModel):
    articles: list[NewsRequest]
    language: str = "English"


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "success": True,
        "message": "NewsIQ API is running.",
        "version": "2.0.0",
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database": "connected",
        "ai": "configured",
    }


# =========================================================
# SAVED NEWS
# =========================================================

@app.get("/saved-news")
def get_saved_news(limit: int = 20):
    limit = max(1, min(limit, 50))

    db = SessionLocal()

    try:
        articles = db.scalars(
            select(Article)
            .order_by(
                Article.created_at.desc()
            )
            .limit(limit)
        ).all()

        results = []

        for article in articles:
            summary = db.scalar(
                select(Summary)
                .where(Summary.article_id == article.id)
                .order_by(Summary.created_at.desc())
            )

            item = article_to_dict(article)

            item["summary"] = (
                summary.summary
                if summary
                else None
            )

            item["summary_language"] = (
                summary.language
                if summary
                else None
            )

            results.append(item)

        return {
            "success": True,
            "count": len(results),
            "articles": results,
        }

    except Exception as e:
        print("Saved news error:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch saved news.",
        )

    finally:
        db.close()


# =========================================================
# ARTICLES - DATABASE API
# =========================================================

@app.get("/articles")
def get_articles(
    category: str | None = None,
    q: str | None = None,
    limit: int = 20,
):
    limit = max(1, min(limit, 100))

    db = SessionLocal()

    try:
        filters = []

        if category and category.strip():
            filters.append(
                Article.category == category.strip().lower()
            )

        if q and q.strip():
            search_term = f"%{q.strip()}%"

            filters.append(
                or_(
                    Article.title.ilike(search_term),
                    Article.description.ilike(search_term),
                    Article.source.ilike(search_term),
                )
            )

        stmt = select(Article)

        if filters:
            stmt = stmt.where(*filters)

        stmt = (
            stmt
            .order_by(
                desc(Article.published_at),
                desc(Article.created_at),
            )
            .limit(limit)
        )

        articles = db.scalars(stmt).all()

        return {
            "success": True,
            "count": len(articles),
            "articles": [
                article_to_dict(article)
                for article in articles
            ],
        }

    except Exception as e:
        print("Articles endpoint error:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch articles.",
        )

    finally:
        db.close()


# =========================================================
# SINGLE ARTICLE
# =========================================================

@app.get("/articles/{article_id}")
def get_article(article_id: int):
    db = SessionLocal()

    try:
        article = db.get(Article, article_id)

        if not article:
            raise HTTPException(
                status_code=404,
                detail="Article not found.",
            )

        summaries = db.scalars(
            select(Summary)
            .where(Summary.article_id == article.id)
            .order_by(Summary.created_at.desc())
        ).all()

        return {
            "success": True,
            "article": article_to_dict(article),
            "summaries": [
                summary_to_dict(summary)
                for summary in summaries
            ],
        }

    finally:
        db.close()


# =========================================================
# SUMMARIES - DATABASE API
# =========================================================

@app.get("/summaries")
def get_summaries(
    language: str | None = None,
    limit: int = 20,
):
    limit = max(1, min(limit, 100))

    db = SessionLocal()

    try:
        stmt = (
            select(Summary, Article)
            .join(
                Article,
                Summary.article_id == Article.id,
            )
            .order_by(
                Summary.created_at.desc()
            )
            .limit(limit)
        )

        if language and language.strip():
            stmt = stmt.where(
                Summary.language == language.strip()
            )

        rows = db.execute(stmt).all()

        results = []

        for summary, article in rows:
            results.append(
                {
                    **summary_to_dict(summary),
                    "article": article_to_dict(article),
                }
            )

        return {
            "success": True,
            "count": len(results),
            "summaries": results,
        }

    except Exception as e:
        print("Summaries endpoint error:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch summaries.",
        )

    finally:
        db.close()


# =========================================================
# DATABASE STATS
# =========================================================

@app.get("/stats")
def get_stats():
    db = SessionLocal()

    try:
        total_articles = (
            db.scalar(
                select(func.count(Article.id))
            )
            or 0
        )

        total_summaries = (
            db.scalar(
                select(func.count(Summary.id))
            )
            or 0
        )

        category_rows = db.execute(
            select(
                Article.category,
                func.count(Article.id),
            )
            .where(
                Article.category.is_not(None)
            )
            .group_by(Article.category)
            .order_by(
                func.count(Article.id).desc()
            )
        ).all()

        category_counts = {
            category: count
            for category, count in category_rows
        }

        return {
            "success": True,
            "stats": {
                "total_articles": total_articles,
                "total_summaries": total_summaries,
                "categories": category_counts,
            },
        }

    except Exception as e:
        print("Stats endpoint error:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch database stats.",
        )

    finally:
        db.close()


# =========================================================
# NEWS API
# =========================================================

@app.get("/news")
def get_news(
    category: str = "technology",
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
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") != "ok":
            raise HTTPException(
                status_code=502,
                detail=data.get(
                    "message",
                    "NewsAPI request failed.",
                ),
            )

        articles = data.get("articles", [])

        save_articles_to_db(
            articles,
            category=category,
        )

        return {
            "success": True,
            "totalResults": data.get(
                "totalResults",
                0,
            ),
            "articles": articles,
        }

    except HTTPException:
        raise

    except requests.RequestException as e:
        print("NewsAPI request error:", repr(e))

        raise HTTPException(
            status_code=502,
            detail="Unable to fetch news from NewsAPI.",
        )


# =========================================================
# SEARCH NEWS
# =========================================================

@app.get("/search")
def search_news(
    q: str,
):
    if not q or not q.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty.",
        )

    query = q.strip()

    normalized_query = re.sub(
        r"\s+",
        " ",
        query,
    ).strip()

    normalized_query = normalized_query.replace(
        "mens",
        "men's",
    )

    normalized_query = normalized_query.replace(
        "womens",
        "women's",
    )

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": normalized_query,
        "sortBy": "relevancy",
        "language": "en",
        "pageSize": 20,
        "apiKey": NEWS_API_KEY,
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") != "ok":
            raise HTTPException(
                status_code=502,
                detail=data.get(
                    "message",
                    "NewsAPI search failed.",
                ),
            )

        articles = data.get(
            "articles",
            [],
        )

        query_words = [
            word.lower()
            for word in re.findall(
                r"[a-zA-Z0-9']+",
                normalized_query,
            )
            if len(word) > 2
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

            text = f"{title} {description}"

            if not query_words:
                relevant_articles.append(article)
                continue

            if any(
                word in text
                for word in query_words
            ):
                relevant_articles.append(article)

        save_articles_to_db(
            relevant_articles
        )

        return {
            "success": True,
            "query": normalized_query,
            "totalResults": len(
                relevant_articles
            ),
            "articles": relevant_articles,
        }

    except HTTPException:
        raise

    except requests.RequestException as e:
        print("NewsAPI search error:", repr(e))

        raise HTTPException(
            status_code=502,
            detail="Unable to search news.",
        )


# =========================================================
# AI SUMMARY PARSER
# =========================================================

def parse_ai_summaries(
    text: str,
    expected_count: int,
):
    if not text:
        return []

    text = text.strip()

    sections = re.split(
        r"(?=ARTICLE\s+\d+)",
        text,
        flags=re.IGNORECASE,
    )

    summaries = []

    for section in sections:
        section = section.strip()

        if not section:
            continue

        section = re.sub(
            r"^ARTICLE\s+\d+\s*:?\s*",
            "",
            section,
            flags=re.IGNORECASE,
        )

        bullets = re.findall(
            r"(?m)^\s*[-•*]\s*(.+)$",
            section,
        )

        if bullets:
            cleaned = "\n".join(
                f"- {bullet.strip()}"
                for bullet in bullets[:5]
                if bullet.strip()
            )

            if cleaned:
                summaries.append(cleaned)

    if len(summaries) >= expected_count:
        return summaries[:expected_count]

    fallback_blocks = re.split(
        r"\n\s*\n",
        text,
    )

    fallback_summaries = []

    for block in fallback_blocks:
        lines = []

        for line in block.splitlines():
            line = line.strip()

            line = re.sub(
                r"^ARTICLE\s+\d+\s*:?\s*",
                "",
                line,
                flags=re.IGNORECASE,
            )

            line = re.sub(
                r"^[-•*]\s*",
                "",
                line,
            )

            if line:
                lines.append(line)

        if lines:
            fallback_summaries.append(
                "\n".join(
                    f"- {line}"
                    for line in lines[:5]
                )
            )

    if fallback_summaries:
        return fallback_summaries[
            :expected_count
        ]

    return []


# =========================================================
# AI SUMMARY
# =========================================================

@app.post("/summarize-batch")
def summarize_news_batch(
    request: BatchNewsRequest,
):
    if not request.articles:
        raise HTTPException(
            status_code=400,
            detail="At least one article is required.",
        )

    if len(request.articles) > 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum 5 articles allowed per request.",
        )

    language = (
        request.language.strip()
        or "English"
    )

    summaries = [None] * len(
        request.articles
    )

    articles_needing_ai = []

    # -----------------------------------------------------
    # CHECK MEMORY CACHE + DATABASE CACHE
    # -----------------------------------------------------

    for index, article in enumerate(
        request.articles
    ):
        title = article.title.strip()
        description = (
            article.description.strip()
        )

        cached = get_cached_summary(
            title,
            description,
            language,
        )

        if cached:
            summaries[index] = cached
            continue

        db_cached = None

        if article.url:
            db_cached = get_db_cached_summary(
                article.url,
                language,
            )

        if db_cached:
            summaries[index] = db_cached

            save_cached_summary(
                title,
                description,
                db_cached,
                language,
            )

            continue

        articles_needing_ai.append(
            (
                index,
                article,
            )
        )

    # -----------------------------------------------------
    # EVERYTHING CACHED
    # -----------------------------------------------------

    if not articles_needing_ai:
        return {
            "success": True,
            "summaries": summaries,
            "cached": True,
        }

    # -----------------------------------------------------
    # BUILD AI PROMPT
    # -----------------------------------------------------

    prompt_parts = [
        f"""
You are an AI news summarization assistant.

Summarize each article in {language}.

For every article:
- Give exactly 5 concise bullet points.
- Use simple and easy language.
- Keep only the most important information.
- Do not invent facts.
- Do not add a conclusion.
- Keep the meaning of the original article.

IMPORTANT:
Return the result using exactly this format:

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

Continue this format for every article.
""".strip()
    ]

    for position, (
        index,
        article,
    ) in enumerate(
        articles_needing_ai,
        start=1,
    ):
        prompt_parts.append(
            f"""
ARTICLE {position}

Title:
{article.title}

Description:
{article.description}
""".strip()
        )

    prompt = "\n\n".join(prompt_parts)

    ai_text = None
    ai_provider = None

    # -----------------------------------------------------
    # GEMINI
    # -----------------------------------------------------

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )

        ai_text = (
            response.text
            if response and response.text
            else None
        )

        if ai_text:
            ai_provider = "gemini"

    except Exception as e:
        print(
            "Gemini summary failed:",
            repr(e),
        )

    # -----------------------------------------------------
    # GROQ FALLBACK
    # -----------------------------------------------------

    if not ai_text:

        try:
            response = groq_client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.2,
            )

            ai_text = (
                response.choices[0]
                .message.content
            )

            if ai_text:
                ai_provider = "groq"

        except Exception as e:
            print(
                "Groq summary failed:",
                repr(e),
            )

    if not ai_text:
        raise HTTPException(
            status_code=502,
            detail="Both Gemini and Groq failed to generate summaries.",
        )

    # -----------------------------------------------------
    # PARSE AI RESPONSE
    # -----------------------------------------------------

    parsed_summaries = parse_ai_summaries(
        ai_text,
        len(articles_needing_ai),
    )

    if not parsed_summaries:
        raise HTTPException(
            status_code=502,
            detail="AI returned an unreadable summary format.",
        )

    # -----------------------------------------------------
    # SAVE SUMMARIES
    # -----------------------------------------------------

    for position, (
        index,
        article,
    ) in enumerate(
        articles_needing_ai
    ):

        if position >= len(
            parsed_summaries
        ):
            break

        summary_text = parsed_summaries[
            position
        ]

        summaries[index] = summary_text

        save_cached_summary(
            article.title,
            article.description,
            summary_text,
            language,
        )

        if article.url:
            save_summary_to_db(
                article.url,
                summary_text,
                language,
            )

    # -----------------------------------------------------
    # FINAL RESPONSE
    # -----------------------------------------------------

    return {
        "success": True,
        "summaries": summaries,
        "cached": False,
        "provider": ai_provider,
    }