import { FaSearch } from "react-icons/fa";
import CategoryCard from "../components/CategoryCard";
import NewsCard from "../components/NewsCard";

function Home() {
  return (
    <div className="min-h-screen bg-black text-white">

      {/* Hero Section */}
      <section className="flex flex-col items-center justify-center text-center px-6 pt-24">

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

        {/* Search Bar */}

        <div className="mt-12 w-full max-w-4xl flex">

          <input
            type="text"
            placeholder="Search any news..."
            className="flex-1 px-6 py-5 bg-zinc-900 rounded-l-xl outline-none text-white text-lg"
          />

          <button className="bg-blue-600 hover:bg-blue-700 px-8 rounded-r-xl transition">
            <FaSearch size={22} />
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
          <CategoryCard title="Health" />
          <CategoryCard title="Science" />

        </div>

      </section>

      {/* Trending News */}

      <section className="mt-24 px-6 pb-20">

        <h2 className="text-4xl font-bold text-center mb-12">
          🔥 Trending News
        </h2>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">

          <NewsCard
            title="AI is Transforming Healthcare"
            source="BBC News"
            description="Artificial Intelligence is helping doctors diagnose diseases faster and more accurately."
          />

          <NewsCard
            title="OpenAI launches new AI Model"
            source="TechCrunch"
            description="The latest OpenAI model improves reasoning, coding and multilingual performance."
          />

          <NewsCard
            title="NASA uses AI for Space Missions"
            source="NASA"
            description="NASA is integrating AI systems to improve mission planning and autonomous spacecraft operations."
          />

        </div>

      </section>

    </div>
  );
}

export default Home;