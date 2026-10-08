function Navbar({ activePage, setActivePage }) {
  const navItems = ["Home", "Categories", "AI Summary", "About"];

  return (
    <nav className="bg-zinc-900 border-b border-zinc-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        <button
          onClick={() => setActivePage("Home")}
          className="text-3xl font-bold text-blue-500 hover:text-blue-400 transition"
        >
          NewsIQ
        </button>

        <ul className="flex gap-8 text-gray-300">
          {navItems.map((item) => (
            <li key={item}>
              <button
                onClick={() => setActivePage(item)}
                className={`transition ${
                  activePage === item
                    ? "text-blue-500 font-semibold"
                    : "hover:text-blue-500"
                }`}
              >
                {item}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;