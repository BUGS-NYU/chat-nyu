import "./App.css";
import { useState, useEffect, useRef } from "react";

function App() {
  const [outputs, setOutputs] = useState([]);

  const [input, setInput] = useState("");
  const outputRef = useRef(null);

  useEffect(() => {
    // TEST
    setOutputs([
      "Hello, world!",
      "This is a test message.",
      "How are you doing today?",
    ]);

    // TEST
    setInterval(() => {
      setOutputs((prevOutputs) => [...prevOutputs, "This is a new message."]);
    }, 2000);
  }, []);

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [outputs]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() === "") {
      return;
    }
    setOutputs((prevOutputs) => [...prevOutputs, `You: ${input}`]);
    setInput("");
  };

  return (
    <div className="home">
      {/* Header */}
      <div className="header">
        <h1> ChatNYU </h1>
      </div>

      {/* Output */}
      <div className="output">
        {outputs.map((output, index) => (
          <div key={index} className="output-item">
            <p>{output}</p>
          </div>
        ))}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="chat-input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter your prompt here..."
          className="chat-input"
        />
        <button type="submit" className="send-button">
          ➝
        </button>
      </form>
    </div>
  );
}

export default App;
