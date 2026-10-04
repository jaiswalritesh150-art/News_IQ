const AI_API_URL =
  import.meta.env.VITE_AI_API_URL || "http://127.0.0.1:8000";

// --------------------------------------------------
// Fetch Top Headlines
// --------------------------------------------------

export async function fetchTopHeadlines(category = "technology") {
  console.log("Fetching Category:", category);

  try {
    const response = await fetch(
      `${AI_API_URL}/news?category=${encodeURIComponent(category)}`
    );

    if (!response.ok) {
      throw new Error(`News API request failed: ${response.status}`);
    }

    const data = await response.json();

    if (!data.success) {
      console.error("News Error:", data);
      return [];
    }

    return data.articles || [];
  } catch (error) {
    console.error("Failed to fetch headlines:", error);
    return [];
  }
}


// --------------------------------------------------
// Search News
// --------------------------------------------------

export async function searchNews(query) {
  console.log("Searching:", query);

  try {
    const response = await fetch(
      `${AI_API_URL}/search?q=${encodeURIComponent(query)}`
    );

    if (!response.ok) {
      throw new Error(`Search request failed: ${response.status}`);
    }

    const data = await response.json();

    if (!data.success) {
      console.error("Search Error:", data);
      return [];
    }

    return data.articles || [];
  } catch (error) {
    console.error("Failed to search news:", error);
    return [];
  }
}


// --------------------------------------------------
// AI Summary
// --------------------------------------------------

export async function summarizeNews(title, description) {
  try {
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

    if (!response.ok) {
      throw new Error(`Summary request failed: ${response.status}`);
    }

    const data = await response.json();

    if (!data.success) {
      console.error("Summary Error:", data);
      return null;
    }

    return data.summary;
  } catch (error) {
    console.error("Failed to generate AI summary:", error);
    return null;
  }
}