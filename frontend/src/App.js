import './App.css';
import { useState, useEffect } from 'react';

function App() {
  const [outputs, setOutputs] = useState([]);

  useEffect(() => {
    // TEST
    setOutputs([
      "Hello, world!",
      "This is a test message.",
      "How are you doing today?",
    ]);

    // TEST
    setInterval(() => {
      setOutputs((prevOutputs) => [
        ...prevOutputs,
        "This is a new message.",
      ]);
    }, 2000);
  }, []);

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
    </div>
  );
}

export default App;
