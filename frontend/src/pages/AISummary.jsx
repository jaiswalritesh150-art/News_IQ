import { useEffect, useState } from "react";

import {
  fetchTopHeadlines,
  summarizeNewsBatch,
} from "../services/newsApi";

function AISummary() {
  const [category, setCategory] = useState("technology");
  const [articles, setArticles] = useState([]);
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(false);

  const categories = [
    { name: "Technology", value: "technology" },
    { name: "Business", value: "business" },
    { name: "Sports", value: "sports" },
    { name: "Science", value: "science" },
    { name: "Health", value: "health" },
    { name: "General", value: "general" },
  ];

  useEffect(() => {
    generateSummaries();
  }, [category]);

  async function generateSummaries() {
    setLoading(true);
    setArticles([]);
    setSummaries([]);

    try {
      const news = await fetchTopHeadlines(category);

      const selectedArticles = (news || []).slice(0, 5);

      setArticles(selectedArticles);

      if (selectedArticles.length === 0) {
        return;
      }

      const result = await summarizeNewsBatch(
        selectedArticles
      );

      setSummaries(result || []);
    } catch (error) {
      console.error(
        "Failed to generate AI summaries:",
        error
      );

      setArticles([]);
      setSummaries([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-black text-white px-6 py-16">

      <div className="max-w-6xl mx-auto">

        {/* HEADER */}

        <div className="text-center mb-12">

          <p className="text-blue-500 font-semibold uppercase tracking-wider mb-3">
            Generative AI
          </p>

          <h1 className="text-5xl md:text-6xl font-extrabold">
            AI News Summary
          </h1>

          <p className="text-gray-400 max-w-2xl mx-auto mt-5 text-lg">
            Get the most important points from the latest news
            without reading the entire article.
          </p>

        </div>


        {/* CATEGORY SELECTOR */}

        <div className="flex flex-wrap justify-center gap-3 mb-14">

          {categories.map((item) => (
            <button
              key={item.value}
              onClick={() => setCategory(item.value)}
              className={`px-5 py-3 rounded-lg font-medium transition ${
                category === item.value
                  ? "bg-blue-600 text-white"
                  : "bg-zinc-900 text-gray-400 hover:text-white hover:bg-zinc-800"
              }`}
            >
              {item.name}
            </button>
          ))}

        </div>


        {/* LOADING */}

        {loading && (
          <div className="text-center py-20">

            <div className="text-5xl mb-5">
              ✨
            </div>

            <h2 className="text-2xl font-semibold">
              AI is summarizing the latest news...
            </h2>

            <p className="text-gray-500 mt-3">
              Fetching articles and generating concise insights.
            </p>

          </div>
        )}


        {/* EMPTY */}

        {!loading && articles.length === 0 && (
          <div className="text-center py-20">

            <p className="text-gray-400 text-lg">
              No articles available right now.
            </p>

            <button
              onClick={generateSummaries}
              className="mt-5 bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg transition"
            >
              Try Again
            </button>

          </div>
        )}


        {/* SUMMARY CARDS */}

        {!loading && articles.length > 0 && (
          <div className="space-y-8">

            {articles.map((article, index) => {

              const summary = summaries[index] || "";

              return (
                <article
                  key={article.url || index}
                  className="bg-zinc-900 border border-zinc-800 rounded-2xl p-7 hover:border-blue-900 transition"
                >

                  {/* SOURCE */}

                  <p className="text-blue-400 text-xs font-semibold uppercase tracking-wider mb-3">
                    {article.source?.name ||
                      article.source ||
                      "News Source"}
                  </p>


                  {/* TITLE */}

                  <h2 className="text-2xl font-bold leading-snug mb-4">
                    {article.title}
                  </h2>


                  {/* DESCRIPTION */}

                  <p className="text-gray-400 leading-relaxed mb-6">
                    {article.description ||
                      "No description available."}
                  </p>


                  {/* AI SUMMARY */}

                  <div className="bg-zinc-950 border border-blue-900/50 rounded-xl p-6">

                    <div className="flex items-center gap-2 mb-5">

                      <span className="text-xl">
                        ✨
                      </span>

                      <h3 className="text-blue-400 font-semibold text-lg">
                        AI Summary
                      </h3>

                    </div>


                    {summary ? (
                      <div className="text-gray-300 leading-relaxed whitespace-pre-line">
                        {summary}
                      </div>
                    ) : (
                      <p className="text-gray-500">
                        Summary unavailable.
                      </p>
                    )}

                  </div>


                  {/* ARTICLE LINK */}

                  {article.url && (
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex mt-5 bg-blue-600 hover:bg-blue-700 px-5 py-3 rounded-lg text-sm font-semibold transition"
                    >
                      Read Full Article ↗
                    </a>
                  )}

                </article>
              );
            })}

          </div>
        )}

      </div>

    </div>
  );
}

export default AISummary;