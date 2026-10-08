function About() {
  return (
    <div className="min-h-screen bg-black text-white px-6 py-16">

      <div className="max-w-6xl mx-auto">

        {/* HERO */}

        <section className="text-center">

          <p className="text-blue-500 font-semibold uppercase tracking-wider mb-3">
            About NewsIQ
          </p>

          <h1 className="text-5xl md:text-6xl font-extrabold">
            Understand News.
            <span className="text-blue-500"> Faster.</span>
          </h1>

          <p className="text-gray-400 max-w-3xl mx-auto mt-6 text-lg leading-relaxed">
            NewsIQ is an AI-powered news platform designed to help
            people understand the latest news quickly through
            concise, simple and easy-to-understand summaries.
          </p>

        </section>


        {/* WHAT IS NEWSIQ */}

        <section className="mt-20 grid md:grid-cols-2 gap-10">

          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8">

            <div className="text-4xl mb-5">
              📰
            </div>

            <h2 className="text-2xl font-bold mb-4">
              What is NewsIQ?
            </h2>

            <p className="text-gray-400 leading-relaxed">
              NewsIQ collects current news from multiple categories
              and presents important information in a simple format.
              Users can search for specific topics, explore categories
              and read AI-generated summaries without going through
              lengthy articles.
            </p>

          </div>


          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8">

            <div className="text-4xl mb-5">
              🤖
            </div>

            <h2 className="text-2xl font-bold mb-4">
              Powered by Generative AI
            </h2>

            <p className="text-gray-400 leading-relaxed">
              NewsIQ uses Generative AI to transform complex news
              content into concise and understandable insights.
              The platform also uses an AI fallback system to keep
              summary generation reliable when the primary AI service
              is temporarily unavailable.
            </p>

          </div>

        </section>


        {/* FEATURES */}

        <section className="mt-20">

          <h2 className="text-3xl font-bold text-center mb-10">
            What You Can Do
          </h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">

            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <div className="text-3xl mb-4">🔎</div>

              <h3 className="font-bold text-lg mb-2">
                Smart Search
              </h3>

              <p className="text-gray-400 text-sm leading-relaxed">
                Search for news using keywords and discover
                relevant articles quickly.
              </p>
            </div>


            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <div className="text-3xl mb-4">📚</div>

              <h3 className="font-bold text-lg mb-2">
                Categories
              </h3>

              <p className="text-gray-400 text-sm leading-relaxed">
                Explore technology, business, sports, science,
                health and general news.
              </p>
            </div>


            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <div className="text-3xl mb-4">✨</div>

              <h3 className="font-bold text-lg mb-2">
                AI Summaries
              </h3>

              <p className="text-gray-400 text-sm leading-relaxed">
                Understand the key points of an article through
                concise AI-generated summaries.
              </p>
            </div>


            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <div className="text-3xl mb-4">⚡</div>

              <h3 className="font-bold text-lg mb-2">
                Fast Experience
              </h3>

              <p className="text-gray-400 text-sm leading-relaxed">
                Get current news and AI insights through a simple,
                responsive interface.
              </p>
            </div>

          </div>

        </section>


        {/* TECHNOLOGY STACK */}

        <section className="mt-20">

          <h2 className="text-3xl font-bold text-center mb-10">
            Technology Behind NewsIQ
          </h2>

          <div className="flex flex-wrap justify-center gap-4">

            {[
              "React",
              "Vite",
              "Tailwind CSS",
              "FastAPI",
              "Python",
              "Generative AI",
              "Gemini",
              "Groq",
              "PostgreSQL",
              "SQLAlchemy",
            ].map((technology) => (
              <span
                key={technology}
                className="bg-zinc-900 border border-zinc-800 px-5 py-3 rounded-lg text-gray-300"
              >
                {technology}
              </span>
            ))}

          </div>

        </section>


        {/* FOOTER MESSAGE */}

        <section className="mt-20 text-center">

          <div className="bg-zinc-900 border border-blue-900/50 rounded-2xl p-10">

            <h2 className="text-3xl font-bold">
              Stay Informed.
              <span className="text-blue-500">
                {" "}Understand Better.
              </span>
            </h2>

            <p className="text-gray-400 mt-4 max-w-2xl mx-auto">
              NewsIQ is built to make staying informed easier by
              combining real-time news with the power of Generative AI.
            </p>

          </div>

        </section>

      </div>

    </div>
  );
}

export default About;