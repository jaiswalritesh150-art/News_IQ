import { useEffect, useRef, useState } from "react";

import CategoryCard from "../components/CategoryCard";
import NewsCard from "../components/NewsCard";

import {
  fetchTopHeadlines,
  summarizeNewsBatch,
} from "../services/newsApi";

function Categories() {
  const [selectedCategory, setSelectedCategory] = useState("technology");
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);

  const requestIdRef = useRef(0);

  const categories = [
    {
      name: "Technology",
      value: "technology",
    },
    {
      name: "Business",
      value: "business",
    },
    {
      name: "Sports",
      value: "sports",
    },
    {
      name: "Science",
      value: "science",
    },
    {
      name: "Health",
      value: "health",
    },
    {
      name: "General",
      value: "general",
    },
  ];

  useEffect(() => {
    loadCategoryNews();
  }, [selectedCategory]);

  async function loadCategoryNews() {
    const requestId = ++requestIdRef.current;

    setLoading(true);
    setNews([]);

    try {
      const articles = await fetchTopHeadlines(selectedCategory);

      if (requestId !== requestIdRef.current) {
        return;
      }

      const selectedArticles = (articles || []).slice(0, 6);

      setNews(selectedArticles);

      if (selectedArticles.length > 0) {
        const summaries = await summarizeNewsBatch(
          selectedArticles
        );

        if (requestId !== requestIdRef.current) {
          return;
        }

        const articlesWithSummaries =
          selectedArticles.map((article, index) => ({
            ...article,
            summary: summaries[index] || "",
          }));

        setNews(articlesWithSummaries);
      }
    } catch (error) {
      if (requestId !== requestIdRef.current) {
        return;
      }

      console.error(
        "Failed to load category news:",
        error
      );

      setNews([]);
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }

  return (
    <div className="min-h-screen bg-black text-white px-6 py-16">
      <div className="max-w-7xl mx-auto">

        {/* HEADER */}

        <div className="text-center mb-14">

          <p className="text-blue-500 font-semibold uppercase tracking-wider mb-3">
            Explore News
          </p>

          <h1 className="text-5xl md:text-6xl font-extrabold">
            News Categories
          </h1>

          <p className="text-gray-400 max-w-2xl mx-auto mt-5">
            Explore the latest stories across different categories
            and understand them instantly with AI-powered summaries.
          </p>

        </div>


        {/* CATEGORY BUTTONS */}

        <div className="flex flex-wrap justify-center gap-5 mb-16">

          {categories.map((category) => (
            <div
              key={category.value}
              className={
                selectedCategory === category.value
                  ? "ring-2 ring-blue-500 rounded-xl"
                  : ""
              }
            >
              <CategoryCard
                title={category.name}
                onClick={() =>
                  setSelectedCategory(category.value)
                }
              />
            </div>
          ))}

        </div>


        {/* CURRENT CATEGORY */}

        <div className="flex items-center justify-between mb-8">

          <div>
            <p className="text-gray-500 text-sm">
              Showing latest news from
            </p>

            <h2 className="text-3xl font-bold capitalize">
              {selectedCategory}
            </h2>
          </div>

          {!loading && news.length > 0 && (
            <span className="text-sm text-gray-500">
              {news.length} articles
            </span>
          )}

        </div>


        {/* LOADING */}

        {loading && (
          <div className="text-center py-20">

            <div className="text-4xl mb-4">
              ✨
            </div>

            <h3 className="text-xl font-semibold">
              Fetching latest news...
            </h3>

            <p className="text-gray-500 mt-2">
              Generating AI summaries for you.
            </p>

          </div>
        )}


        {/* NO NEWS */}

        {!loading && news.length === 0 && (
          <div className="text-center py-20">

            <p className="text-gray-400 text-lg">
              No news found for this category.
            </p>

            <button
              onClick={loadCategoryNews}
              className="mt-5 bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg transition"
            >
              Try Again
            </button>

          </div>
        )}


        {/* NEWS GRID */}

        {!loading && news.length > 0 && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">

            {news.map((article, index) => (
              <NewsCard
                key={article.url || index}
                title={article.title}
                source={article.source?.name}
                description={article.description}
                image={article.urlToImage}
                url={article.url}
                summary={article.summary}
              />
            ))}

          </div>
        )}

      </div>
    </div>
  );
}

export default Categories;