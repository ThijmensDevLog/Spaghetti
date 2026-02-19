import { useState } from "react";

function App() {
  const [workflow, setWorkflow] = useState(`{
    "start": "1",
    "steps": {
        "1": {"type": "set", "key": "temperature", "value": 22, "next": ["2"]},
        "2": {
            "type": "if",
            "condition": "data.get('temperature', 0) > 25",
            "true_next": ["3"],
            "false_next": ["4"]
        },
        "3": {"type": "log", "message": "It's hot!", "next": ["5"]},
        "4": {"type": "log", "message": "It's cool!", "next": ["5"]},
        "5": {
            "type": "http",
            "url": "https://jsonplaceholder.typicode.com/todos/1",
            "method": "GET",
            "store_key": "todo",
            "next": []
        }
    }
}`);

    const [output, setOutput] = useState("");

    async function runWorkflow() {
      try {
        const parsedWorkflow = JSON.parse(workflow);

        const response = await fetch("http://127.0.0.1:8000/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(parsedWorkflow)
        });
        const data = await response.json();
        setOutput(JSON.stringify(data, null, 2));
      } catch (err) {
        setOutput("Error: " + err);
      }
    }

    return (
      <div style={{ padding: "20px" }}>
        <h1>Spaghetti</h1>
        <textarea
          rows="20"
          cols="80"
          value={workflow}
          onChange={(e) => setWorkflow(e.target.value)}
        />
        <br />
        <button onClick={runWorkflow} style={{ marginTop: "10px" }}>
          Run Workflow
        </button>
        <h2>Output:</h2>
        <pre>{output}</pre>
      </div>
    );
}

export default App;