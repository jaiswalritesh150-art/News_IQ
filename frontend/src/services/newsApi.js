export async function fetchTopHeadlines(category = "technology") {
  console.log("Fetching:", category);

  const response = await fetch(
    `${BASE_URL}/top-headlines?country=us&category=${category}&apiKey=${API_KEY}`
  );

  console.log("Status:", response.status);

  const data = await response.json();

  console.log(data);

  return data.articles;
}