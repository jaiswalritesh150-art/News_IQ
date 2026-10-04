const API_KEY = import.meta.env.VITE_NEWS_API_KEY;

const BASE_URL = "https://newsapi.org/v2";
const AI_API_URL = import.meta.env.VITE_AI_API_URL || "http://127.0.0.1:8000";

// Fetch Top Headlines
export async function fetchTopHeadlines(category = "technology") {
  console.log("Fetching Category:", category);

  const response = await fetch(
    `${BASE_URL}/top-headlines?country=us&category=${category}&apiKey=${API_KEY}`
  );

  const data = await response.json();

  if (data.status !== "ok") {
    console.error("News API Error:", data);
    return [];
  }

  return data.articles || [];
}

// Search News
export async function searchNews(query) {
  console.log("Searching:", query);

  const response = await fetch(
    `${BASE_URL}/everything?q=${encodeURIComponent(
      query
    )}&sortBy=publishedAt&language=en&apiKey=${API_KEY}`
  );

  const data = await response.json();

  if (data.status !== "ok") {
    console.error("Search Error:", data);
    return [];
  }

  return data.articles || [];
}

// AI Summary
export async function summarizeNews(title, description) {
  const response = await fetch(`${AI_API_URL}/summarize`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      title,
      description,
    }),
  });

  const data = await response.json();

  console.log(data.success);
  console.log(data.summary);
  console.log(data.error);

  return data.summary;
}
