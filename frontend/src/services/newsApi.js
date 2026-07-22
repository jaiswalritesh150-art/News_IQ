const API_KEY = import.meta.env.VITE_NEWS_API_KEY;

const BASE_URL = "https://newsapi.org/v2";

// Fetch Top Headlines
export async function fetchTopHeadlines(category = "technology") {
  console.log("Fetching:", category);

  const response = await fetch(
    `${BASE_URL}/top-headlines?country=us&category=${category}&apiKey=${API_KEY}`
  );

  const data = await response.json();
  return data.articles || [];
}

// Search News
export async function searchNews(query) {
  const response = await fetch(
    `${BASE_URL}/everything?q=${encodeURIComponent(
      query
    )}&sortBy=publishedAt&language=en&apiKey=${API_KEY}`
  );

  const data = await response.json();
  return data.articles || [];
}

// AI Summary
export async function summarizeNews(title, description) {
  const response = await fetch(
    "http://127.0.0.1:8000/summarize",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title,
        description,
      }),
    }
  );

  const data = await response.json();
  return data.summary;
}