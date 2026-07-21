const API_KEY = import.meta.env.VITE_NEWS_API_KEY;

const BASE_URL = "https://newsapi.org/v2";

export async function fetchTopHeadlines(category = "technology") {
  const response = await fetch(
    `${BASE_URL}/top-headlines?country=us&category=${category}&apiKey=${API_KEY}`
  );

  const data = await response.json();

  return data.articles;
}

export async function searchNews(query) {
  const response = await fetch(
    `${BASE_URL}/everything?q=${query}&sortBy=publishedAt&language=en&apiKey=${API_KEY}`
  );

  const data = await response.json();

  return data.articles;
}