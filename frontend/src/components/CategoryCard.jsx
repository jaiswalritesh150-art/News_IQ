function CategoryCard({ title, onClick }) {
  return (
    <div
      onClick={onClick}
      className="bg-zinc-900 rounded-xl p-5 cursor-pointer hover:bg-zinc-800 hover:border-blue-500 border border-zinc-800 transition duration-300"
    >
      <h3 className="text-white font-semibold">
        {title}
      </h3>
    </div>
  );
}

export default CategoryCard;