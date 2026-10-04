from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from groq import Groq

import os
import re
import requests
import time


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
    api_key=GEMINI_API_KEY
)

groq_client = Groq(
    api_key=GROQ_API_KEY
)


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
            # Gemini Quota Check
            # ------------------------------------------------

            is_quota_error = (
                "429" in gemini_error_text
                or
                "RESOURCE_EXHAUSTED"
                in gemini_error_text
                or
                "quota"
                in gemini_error_text.lower()
            )


            if not is_quota_error:

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


                # ------------------------------------------------
                # Debug Groq Response
                # ------------------------------------------------

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


                # ------------------------------------------------
                # Read Groq Content
                # ------------------------------------------------

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


                # ------------------------------------------------
                # Some Groq responses may expose useful
                # generated text through reasoning/content.
                # Prefer content, then reasoning as fallback.
                # ------------------------------------------------

                if content:

                    raw_summary = content.strip()

                elif reasoning:

                    raw_summary = reasoning.strip()

                else:

                    # Print complete response only when
                    # both fields are empty.
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

        for position in range(
            1,
            len(articles_needing_ai) + 1
        ):

            marker = f"ARTICLE {position}"

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

                section = raw_summary[start:]

            else:

                section = raw_summary[
                    start:end
                ]


            section = section.strip()


            # ------------------------------------------------
            # Clean accidental markdown fences
            # ------------------------------------------------

            section = re.sub(
                r"```(?:text|markdown)?",
                "",
                section,
                flags=re.IGNORECASE
            )

            section = section.replace(
                "```",
                ""
            )

            section = section.strip()


            if not section:

                section = (
                    "Summary unavailable."
                )


            generated_summaries.append(
                section
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