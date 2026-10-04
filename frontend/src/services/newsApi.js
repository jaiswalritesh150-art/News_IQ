const AI_API_URL =
  import.meta.env.VITE_AI_API_URL ||
  "http://127.0.0.1:8000";


// --------------------------------------------------
// Fetch Top Headlines
// --------------------------------------------------

export async function fetchTopHeadlines(
  category = "technology"
) {
  console.log(
    "Fetching Category:",
    category
  );

  try {
    const response = await fetch(
      `${AI_API_URL}/news?category=${encodeURIComponent(
        category
      )}`
    );

    if (!response.ok) {
      throw new Error(
        `News API request failed: ${response.status}`
      );
    }

    const data = await response.json();

    if (!data.success) {
      console.error(
        "News Error:",
        data
      );

      return [];
    }

    return data.articles || [];

  } catch (error) {
    console.error(
      "Failed to fetch headlines:",
      error
    );

    return [];
  }
}


// --------------------------------------------------
// Search News
// --------------------------------------------------

export async function searchNews(query) {
  console.log(
    "Searching:",
    query
  );

  try {
    const response = await fetch(
      `${AI_API_URL}/search?q=${encodeURIComponent(
        query
      )}`
    );

    if (!response.ok) {
      throw new Error(
        `Search request failed: ${response.status}`
      );
    }

    const data = await response.json();

    if (!data.success) {
      console.error(
        "Search Error:",
        data
      );

      return [];
    }

    return data.articles || [];

  } catch (error) {
    console.error(
      "Failed to search news:",
      error
    );

    return [];
  }
}


// --------------------------------------------------
// Batch Summary Request Control
// --------------------------------------------------

let activeBatchRequest = null;

let activeBatchKey = "";


// --------------------------------------------------
// Create Batch Key
// --------------------------------------------------

function createBatchKey(articles) {
  return articles
    .slice(0, 5)
    .map((article) => {
      return [
        article.title || "",
        article.description || "",
      ].join("::");
    })
    .join("||");
}


// --------------------------------------------------
// AI Batch News Summarization
// --------------------------------------------------

export async function summarizeNewsBatch(
  articles
) {
  if (
    !articles ||
    articles.length === 0
  ) {
    return [];
  }


  // --------------------------------------------------
  // Limit to 5 articles
  // --------------------------------------------------

  const selectedArticles =
    articles.slice(0, 5);


  // --------------------------------------------------
  // Create unique request key
  // --------------------------------------------------

  const batchKey =
    createBatchKey(
      selectedArticles
    );


  // --------------------------------------------------
  // Prevent duplicate simultaneous requests
  // --------------------------------------------------

  if (
    activeBatchRequest &&
    activeBatchKey === batchKey
  ) {
    console.log(
      "Reusing active batch summary request."
    );

    return activeBatchRequest;
  }


  // --------------------------------------------------
  // Create one batch request
  // --------------------------------------------------

  activeBatchKey = batchKey;

  activeBatchRequest = (async () => {

    try {

      console.log(
        `Generating AI summaries for ${selectedArticles.length} articles...`
      );


      const response = await fetch(
        `${AI_API_URL}/summarize-batch`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            articles:
              selectedArticles.map(
                (article) => ({
                  title:
                    article.title || "",

                  description:
                    article.description ||
                    "No description available.",
                })
              ),
          }),
        }
      );


      // --------------------------------------------------
      // Gemini quota / rate limit
      // --------------------------------------------------

      if (response.status === 429) {

        console.warn(
          "AI summary quota is temporarily unavailable."
        );

        return [];
      }


      // --------------------------------------------------
      // Other backend errors
      // --------------------------------------------------

      if (!response.ok) {

        const errorText =
          await response.text();

        console.error(
          "Batch summary request failed:",
          response.status,
          errorText
        );

        return [];
      }


      // --------------------------------------------------
      // Parse response
      // --------------------------------------------------

      const data =
        await response.json();


      if (!data.success) {

        console.error(
          "Batch Summary Error:",
          data
        );

        return [];
      }


      const summaries =
        data.summaries || [];


      console.log(
        "AI Summaries received:",
        summaries
      );


      return summaries;

    } catch (error) {

      console.error(
        "Failed to generate batch AI summaries:",
        error
      );

      return [];

    } finally {

      // Allow another different batch request
      activeBatchRequest = null;
      activeBatchKey = "";

    }

  })();


  return activeBatchRequest;
}