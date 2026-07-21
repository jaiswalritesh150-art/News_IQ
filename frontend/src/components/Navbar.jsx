function Navbar() {
  return (
    <nav className="bg-zinc-900 border-b border-zinc-800">
      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">

        <h1 className="text-3xl font-bold text-blue-500">
          NewIQ
        </h1>

        <ul className="flex gap-8 text-gray-300">
          <li className="hover:text-blue-500 cursor-pointer">
            Home
          </li>

          <li className="hover:text-blue-500 cursor-pointer">
            Categories
          </li>

          <li className="hover:text-blue-500 cursor-pointer">
            AI Summary
          </li>

          <li className="hover:text-blue-500 cursor-pointer">
            About
          </li>
        </ul>

      </div>
    </nav>
  );
}

export default Navbar;