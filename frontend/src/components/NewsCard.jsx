function NewsCard({
  title,
  source,
  description,
  image,
  url,
  summary,
}) {

  // Convert AI summary into clean bullet points
  function formatSummary(text) {
    if (!text) {
      return [];
    }

    return text
      // Split when a new bullet starts
      .split(/\s*(?:-|•|\*)\s+/)
      .map((point) => point.trim())
      .filter(Boolean)
      // Remove any remaining bullet characters
      .map((point) =>
        point
          .replace(/^[-•*]+/, "")
          .trim()
      )
      .filter(Boolean);
  }

  const summaryPoints = formatSummary(summary);


  return (
    <article className="bg-zinc-900 rounded-2xl overflow-hidden border border-zinc-800 hover:border-zinc-700 transition duration-300">

      {/* Image */}
      <div className="relative overflow-hidden">
        <img
          src={
            image ||
            "https://via.placeholder.com/400x220?text=NewsIQ"
          }
          alt={title}
          className="w-full h-52 object-cover"
        />
      </div>


      {/* Content */}
      <div className="p-6">

        {/* Source */}
        <p className="text-blue-400 text-xs font-semibold uppercase tracking-wider mb-3">
          {source || "News Source"}
        </p>


        {/* Title */}
        <h3 className="text-xl font-bold text-white leading-snug mb-3 line-clamp-2">
          {title}
        </h3>


        {/* Description */}
        <p className="text-gray-400 text-sm leading-relaxed line-clamp-3">
          {description || "No description available for this article."}
        </p>


        {/* AI Summary */}
        <div className="mt-6 bg-zinc-950 rounded-xl p-5 border border-blue-900/60">

          <div className="flex items-center gap-2 mb-4">
            <span className="text-lg">✨</span>

            <h4 className="text-blue-400 font-semibold">
              AI Summary
            </h4>
          </div>


          {summaryPoints.length > 0 ? (

            <ul className="space-y-3">

              {summaryPoints.slice(0, 5).map(
                (point, index) => (

                  <li
                    key={index}
                    className="flex items-start gap-3 text-gray-300 text-sm leading-relaxed"
                  >

                    <span className="text-blue-400 mt-1 shrink-0">
                      •
                    </span>

                    <span>
                      {point}
                    </span>

                  </li>

                )
              )}

            </ul>

          ) : (

            <p className="text-gray-500 text-sm">
              Summary unavailable.
            </p>

          )}

        </div>


        {/* Read Full Article */}
        {url && (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-5 w-full inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 px-5 py-3 rounded-lg text-sm font-semibold transition"
          >
            Read Full Article
            <span>↗</span>
          </a>
        )}

      </div>
    </article>
  );
}

export default NewsCard;