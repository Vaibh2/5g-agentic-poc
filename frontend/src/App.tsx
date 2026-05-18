import { useState } from "react";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Deploy } from "./pages/Deploy";
import { Workflows } from "./pages/Workflows";
import { Incidents } from "./pages/Incidents";
import { Chat } from "./pages/Chat";

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");

  const renderPage = () => {
    switch (activeTab) {
      case "dashboard":
        return <Dashboard />;
      case "deploy":
        return <Deploy />;
      case "workflows":
        return <Workflows />;
      case "incidents":
        return <Incidents />;
      case "chat":
        return <Chat />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {renderPage()}
    </Layout>
  );
}

export default App;