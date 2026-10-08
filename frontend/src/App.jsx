import { useState } from "react";

import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Categories from "./pages/Categories";
import AISummary from "./pages/AISummary";
import About from "./pages/About";

function App() {
  const [activePage, setActivePage] = useState("Home");

  const renderPage = () => {
    switch (activePage) {
      case "Home":
        return <Home />;

      case "Categories":
        return <Categories />;

      case "AI Summary":
        return <AISummary />;

      case "About":
        return <About />;

      default:
        return <Home />;
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950">
      <Navbar
        activePage={activePage}
        setActivePage={setActivePage}
      />

      {renderPage()}
    </div>
  );
}
export default App;