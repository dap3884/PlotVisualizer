import React, { useState, useEffect } from "react";
import axios from "axios";
import Editor from "@monaco-editor/react";

const CodeEditor = ({ code, setCode, language }) => (
  <div className="h-[calc(100vh-200px)] w-full">
    <Editor
      height="100%"
      language={language}
      value={code}
      onChange={(value) => setCode(value || "")}
      theme="vs-light"
      options={{
        fontSize: 14,
        minimap: { enabled: false },
        automaticLayout: true,
        lineNumbers: "on",
        tabSize: 2,
        scrollbar: { vertical: "hidden", horizontal: "hidden" },
      }}
    />
  </div>
);

const App = () => {
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState("");
  const [chartUrl, setChartUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // Patch for ResizeObserver warning
    const observerErrorHandler = () => {
      try {
        const ro = new ResizeObserver(() => {});
        ro.observe(document.body);
      } catch (e) {}
    };
    observerErrorHandler();
  }, []);

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    setChartUrl("");

    try {
      const response = await axios.post("http://localhost:8000/generate-visualization", {
        language,
        code,
      });
      console.log(response.data)
      setChartUrl("http://localhost:8000" + response.data.chart_url);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#121212] text-white font-sans">
      <header className="bg-[#1e1e1e] text-white p-4 shadow-md">
        <div className="max-w-7xl mx-auto flex justify-center items-center">
          <h1 className="text-2xl font-bold items-center">PlotVisualizer</h1>
        </div>
      </header>

      <div className="flex flex-grow overflow-hidden">
        <div className="w-1/2 p-4 flex flex-col border-r border-gray-800 bg-[#181818]">
          <div className="mb-4 flex gap-4">
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="border border-gray-600 bg-[#252525] text-white p-2 rounded w-1/2*2"
            >
              <option value="python">Python</option>
              <option value="r">R</option>
            </select>
          </div>

          <div className="flex-grow border border-gray-700 rounded overflow-hidden">
            <CodeEditor code={code} setCode={setCode} language={language} />
          </div>

          <button
            onClick={handleGenerate}
            className="mt-4 bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
            disabled={loading || !code}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg
                  className="animate-spin h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8v8H4z"
                  ></path>
                </svg>
                Generating...
              </span>
            ) : (
              "Generate"
            )}
          </button>

          {error && <p className="text-red-500 mt-2">{error}</p>}
        </div>

        <div className="w-1/2 p-4 overflow-auto bg-[#181818] border-l border-gray-800 flex justify-center items-center">
          {loading ? (
            <div className="flex flex-col items-center gap-4 text-gray-400">
              <svg
                className="animate-spin h-10 w-10 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v8H4z"
                ></path>
              </svg>
              <p>Generating chart...</p>
            </div>
          ) : chartUrl && chartUrl.endsWith(".png") ? (
            <img src={chartUrl} alt="Generated Chart" className="w-full border border-gray-700 rounded" />
          ) : chartUrl && chartUrl.endsWith(".html") ? (
            <iframe
              src={chartUrl}
              title="Visualization"
              width="100%"
              height="500px"
              className="border border-gray-700 rounded"
            />
          ) : (
            <p className="text-gray-400 text-center mt-10">Your visualization will appear here</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
