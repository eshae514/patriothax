import "./App.css";
import { useState } from "react";

function App() {
  const [bpm, setBpm] = useState("");
  const [data, setData] = useState(null);

  async function getAdvice() {
    if (!bpm) return;

    const res = await fetch("http://127.0.0.1:8000/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bpm: Number(bpm) })
    });

    const json = await res.json();
    setData(json);
  }

  return (
    <div className="app">
      <h1 className="app-title">Learn from the Heart</h1>

      <input
        type="number"
        className="bpm-input"
        placeholder="Enter heart rate (BPM)"
        value={bpm}
        onChange={(e) => setBpm(e.target.value)}
      />

      <button className="heart-button" onClick={getAdvice}>
        Read My Heart
      </button>

      {data && (
        <div className="card">
          <h2 className="card-title">{data.title}</h2>
          <p className="card-insight">{data.insight}</p>

          <div className="steps">
            {data.steps.map((step, i) => (
              <div key={i} className="step">
                ❤️ {step}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
