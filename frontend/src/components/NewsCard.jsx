function NewsCard({ title, source, description }) {
  return (
    <div className="bg-zinc-900 rounded-xl p-6 border border-zinc-800 hover:border-blue-500 transition">

      <h3 className="text-2xl font-bold mb-3">
        {title}
      </h3>

      <p className="text-blue-400 mb-4">
        {source}
      </p>

      <p className="text-gray-400">
        {description}
      </p>

      <button className="mt-6 bg-blue-600 hover:bg-blue-700 px-5 py-2 rounded-lg">
        Summarize
      </button>

    </div>
  );
}

export default NewsCard;