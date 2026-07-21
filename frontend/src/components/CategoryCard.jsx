function CategoryCard({ title }) {
  return (
    <button className="bg-zinc-900 border border-zinc-700 px-6 py-3 rounded-xl hover:bg-blue-600 transition duration-300">
      {title}
    </button>
  );
}

export default CategoryCard;