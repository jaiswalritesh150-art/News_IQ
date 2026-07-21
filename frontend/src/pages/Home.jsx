import { useState, useEffect } from "react";
import { FaSearch } from "react-icons/fa";

import CategoryCard from "../components/CategoryCard";
import NewsCard from "../components/NewsCard";
import FeatureCard from "../components/FeatureCard";

import { fetchTopHeadlines, searchNews } from "../services/newsApi";

function Home() {
  const [search, setSearch] = useState("");
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNews();
  }, []);

  async function loadNews() {
    setLoading(true);

    try {
      const articles = await fetchTopHeadlines("technology");
      setNews(articles || []);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch() {
    if (!search.trim()) {
      loadNews();
      return;
    }

    setLoading(true);

    try {
      const articles = await searchNews(search);
      setNews(articles || []);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-black text-white">

      {/* Hero */}
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

        {/* Search */}

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

      {/* Categories */}

      <section className="mt-20 px-6">

        <h2 className="text-3xl font-bold text-center mb-8">
          Trending Categories
        </h2>

        <div className="flex flex-wrap justify-center gap-5">

          <CategoryCard title="Technology" />
          <CategoryCard title="Artificial Intelligence" />
          <CategoryCard title="Business" />
          <CategoryCard title="Finance" />
          <CategoryCard title="Sports" />
          <CategoryCard title="Politics" />
          <CategoryCard title="Science" />
          <CategoryCard title="Health" />

        </div>

      </section>

      {/* News */}

      <section className="mt-24 px-6">

        <h2 className="text-4xl font-bold text-center mb-12">
          🔥 Latest Headlines
        </h2>

        {loading ? (

          <h2 className="text-center text-xl">
            Loading News...
          </h2>

        ) : (

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">

            {news.map((article, index) => (
              <NewsCard
                key={index}
                title={article.title}
                source={article.source?.name}
                description={article.description}
                image={article.urlToImage}
                url={article.url}
              />
            ))}

          </div>

        )}

      </section>

      {/* Features */}

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
            title="Multi Language"
            description="Read news in your preferred language."
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