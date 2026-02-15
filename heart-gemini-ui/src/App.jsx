import "./App.css";
import { useState } from "react";

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]); // for BPM history (optional graph later)

  function getAdvice() {
    setLoading(true);
    setData(null);
    setHistory([]);

    const evtSource = new EventSource("http://127.0.0.1:8000/bpm_stream");

    evtSource.onmessage = (event) => {
      const parsed = JSON.parse(event.data);

      if (parsed.bpm) {
        // Update current BPM and history
        setData((prev) => ({ ...prev, bpm: parsed.bpm }));
        setHistory((prev) => [...prev, parsed.bpm]);
      } else if (parsed.ai) {
        // AI advice received
        setData({
          bpm: history[history.length - 1] || 0, // last BPM
          title: parsed.ai.title,
          insight: parsed.ai.insight,
          steps: parsed.ai.steps,
        });
        setLoading(false);
        evtSource.close();
      }
    };

    evtSource.onerror = (err) => {
      console.error("SSE error:", err);
      evtSource.close();
      setLoading(false);
    };
  }

  return (
    <div className="app">
      <h1 className="app-title">💗 Learn from Your Heart</h1>

      <button className="heart-button" onClick={getAdvice}>
        Read My Heart
      </button>

      {loading && <p className="loading">Listening to your heartbeat...</p>}

      {data?.bpm && !data?.title && (
        <p className="bpm-display">❤️ {data.bpm} BPM</p>
      )}

      {data?.title && (
        <div className="card">
          <h2 className="card-title">{data.title}</h2>

          <p className="bpm-display">
            ❤️ {data.bpm} BPM
          </p>

          <p className="card-insight">{data.insight}</p>

          <div className="steps">
            {data.steps.map((step, i) => (
              <div key={i} className="step">
                💕 {step}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
