import { FaBrain, FaGlobe, FaBolt, FaSearch } from "react-icons/fa";

const icons = {
  brain: <FaBrain size={35} />,
  globe: <FaGlobe size={35} />,
  bolt: <FaBolt size={35} />,
  search: <FaSearch size={35} />,
};

function FeatureCard({ icon, title, description }) {
  return (
    <div className="bg-zinc-900 rounded-xl p-8 border border-zinc-800 hover:border-blue-500 transition duration-300">

      <div className="text-blue-500 mb-5">
        {icons[icon]}
      </div>

      <h3 className="text-2xl font-bold text-white mb-3">
        {title}
      </h3>

      <p className="text-gray-400">
        {description}
      </p>

    </div>
  );
}

export default FeatureCard;