import { useState, useEffect, useRef } from "react";
import { FaSearch } from "react-icons/fa";

import CategoryCard from "../components/CategoryCard";
import NewsCard from "../components/NewsCard";
import FeatureCard from "../components/FeatureCard";

import {
  fetchTopHeadlines,
  searchNews,
  summarizeNewsBatch,
} from "../services/newsApi";


function Home() {
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("technology");
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);

  // Used to ignore old/stale API responses
  const requestIdRef = useRef(0);


  // ==================================================
  // LOAD CATEGORY NEWS
  // ==================================================

  useEffect(() => {
    loadNews();
  }, [selectedCategory]);


  async function loadNews() {
    const requestId = ++requestIdRef.current;

    console.log("Selected Category:", selectedCategory);

    setLoading(true);

    try {
      const articles = await fetchTopHeadlines(selectedCategory);

      // Ignore response from an older request
      if (requestId !== requestIdRef.current) {
        return;
      }

      console.log("Articles:", articles);

      const selectedArticles = (articles || []).slice(0, 5);

      // Show news immediately
      setNews(selectedArticles);

      // Generate all summaries in ONE batch request
      if (selectedArticles.length > 0) {
        console.log("Generating batch AI summaries...");

        const summaries = await summarizeNewsBatch(
          selectedArticles
        );

        // Ignore old summary response
        if (requestId !== requestIdRef.current) {
          return;
        }

        console.log("AI Summaries:", summaries);

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

      console.error("Failed to load news:", error);

      setNews([]);

    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }


  // ==================================================
  // SEARCH NEWS
  // ==================================================

  async function handleSearch() {
    const query = search.trim();

    // If search box is empty,
    // load the currently selected category
    if (!query) {
      loadNews();
      return;
    }

    const requestId = ++requestIdRef.current;

    console.log("Searching for:", query);

    setLoading(true);

    try {
      const articles = await searchNews(query);

      // Ignore old search response
      if (requestId !== requestIdRef.current) {
        return;
      }

      console.log("Search Articles:", articles);

      const selectedArticles = (articles || []).slice(0, 5);

      // Show searched news immediately
      setNews(selectedArticles);

      // Generate summaries in ONE batch request
      if (selectedArticles.length > 0) {
        console.log("Generating search AI summaries...");

        const summaries = await summarizeNewsBatch(
          selectedArticles
        );

        // Ignore old summary response
        if (requestId !== requestIdRef.current) {
          return;
        }

        console.log(
          "Search AI Summaries:",
          summaries
        );

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
        "Failed to search news:",
        error
      );

      setNews([]);

    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }


  // ==================================================
  // UI
  // ==================================================

  return (
    <div className="min-h-screen bg-black text-white">

      {/* ==============================================
          HERO
      ============================================== */}

      <section className="flex flex-col items-center text-center px-6 pt-24">

        <h1 className="text-6xl md:text-7xl font-extrabold">
          Understand Every News
        </h1>

        <h2 className="text-6xl md:text-7xl font-extrabold text-blue-500 mt-2">
          In Seconds
        </h2>

        <p className="text-gray-400 max-w-3xl mt-6 text-lg">
          AI-powered platform that summarizes news into simple,
          concise and easy-to-understand insights.
        </p>


        {/* SEARCH */}

        <div className="mt-12 w-full max-w-4xl flex">

          <input
            type="text"
            placeholder="Search any news..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSearch();
              }
            }}
            className="flex-1 px-6 py-5 bg-zinc-900 rounded-l-xl outline-none text-white"
          />

          <button
            onClick={handleSearch}
            className="bg-blue-600 hover:bg-blue-700 px-8 rounded-r-xl transition"
          >
            <FaSearch />
          </button>

        </div>

      </section>


      {/* ==============================================
          CATEGORIES
      ============================================== */}

      <section className="mt-20 px-6">

        <h2 className="text-3xl font-bold text-center mb-8">
          Trending Categories
        </h2>

        <div className="flex flex-wrap justify-center gap-5">

          <CategoryCard
            title="Technology"
            onClick={() => {
              setSelectedCategory("technology");
            }}
          />

          <CategoryCard
            title="Artificial Intelligence"
            onClick={() => {
              setSelectedCategory("technology");
            }}
          />

          <CategoryCard
            title="Business"
            onClick={() => {
              setSelectedCategory("business");
            }}
          />

          <CategoryCard
            title="Finance"
            onClick={() => {
              setSelectedCategory("business");
            }}
          />

          <CategoryCard
            title="Sports"
            onClick={() => {
              setSelectedCategory("sports");
            }}
          />

          <CategoryCard
            title="Politics"
            onClick={() => {
              setSelectedCategory("general");
            }}
          />

          <CategoryCard
            title="Science"
            onClick={() => {
              setSelectedCategory("science");
            }}
          />

          <CategoryCard
            title="Health"
            onClick={() => {
              setSelectedCategory("health");
            }}
          />

        </div>

      </section>


      {/* ==============================================
          NEWS
      ============================================== */}

      <section className="mt-24 px-6">

        <h2 className="text-4xl font-bold text-center mb-12">
          🔥 Latest Headlines
        </h2>


        {/* LOADING */}

        {loading ? (

          <div className="text-center">

            <h2 className="text-xl">
              Loading News...
            </h2>

            <p className="text-gray-500 mt-2">
              Fetching latest news and generating AI summaries...
            </p>

          </div>


        ) : news.length === 0 ? (

          /* NO NEWS */

          <p className="text-center text-gray-500">
            No news found.
          </p>


        ) : (

          /* NEWS GRID */

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">

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

      </section>


      {/* ==============================================
          FEATURES
      ============================================== */}

      <section className="mt-24 px-6 pb-20">

        <h2 className="text-4xl font-bold text-center mb-12">
          Why Choose NewsIQ?
        </h2>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-7xl mx-auto">

          <FeatureCard
            icon="brain"
            title="AI Summary"
            description="Generate concise summaries using AI."
          />

          <FeatureCard
            icon="globe"
            title="Simple English"
            description="Understand complex news in simple language."
          />

          <FeatureCard
            icon="bolt"
            title="Real-Time News"
            description="Always updated with latest headlines."
          />

          <FeatureCard
            icon="search"
            title="Smart Search"
            description="Search news instantly using keywords."
          />

        </div>

      </section>

    </div>
  );
}


export default Home;