import { useState } from "react";
import { summarizeNews } from "../services/newsApi";

function NewsCard({ title, source, description, image, url }) {
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSummary() {
    setLoading(true);

    try {
      const result = await summarizeNews(title, description);
      setSummary(result);
    } catch (error) {
      alert("Failed to generate summary");
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-zinc-900 rounded-xl overflow-hidden border border-zinc-800 hover:border-blue-500 transition duration-300 hover:scale-105">

      {/* Image */}
      <img
        src={
          image ||
          "https://via.placeholder.com/400x220?text=NewsIQ"
        }
        alt={title}
        className="w-full h-52 object-cover"
      />

      <div className="p-6">

        <h3 className="text-xl font-bold text-white mb-3 line-clamp-2">
          {title}
        </h3>

        <p className="text-blue-400 text-sm mb-3">
          {source}
        </p>

        <p className="text-gray-400 line-clamp-3">
          {description || "No description available."}
        </p>

        <div className="flex gap-3 mt-6">

          <button
            onClick={handleSummary}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 px-5 py-2 rounded-lg disabled:bg-gray-600"
          >
            {loading ? "Summarizing..." : "Summarize"}
          </button>

          <a
            href={url}
            target="_blank"
            rel="noreferrer"
            className="bg-zinc-700 hover:bg-zinc-600 px-5 py-2 rounded-lg"
          >
            Read More
          </a>

        </div>

        {summary && (
          <div className="mt-6 bg-zinc-800 rounded-lg p-4 border border-blue-500">
            <h4 className="text-blue-400 font-semibold mb-2">
              ✨ AI Summary
            </h4>

            <p className="text-gray-300 whitespace-pre-wrap">
              {summary}
            </p>
          </div>
        )}

      </div>

    </div>
  );
}

export default NewsCard;