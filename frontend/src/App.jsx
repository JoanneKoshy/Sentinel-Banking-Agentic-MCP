import { useState, useRef, useEffect } from "react";
import Login from "./Login";
import "./App.css";

const API_URL = "http://127.0.0.1:8080/chat";

const QUICK_ACTIONS = [
  { label: "Check balance", message: "What is my current balance?", color: "qa-green" },
  { label: "Recent transactions", message: "Show me my last 5 transactions", color: "qa-blue" },
  { label: "Request cheque book", message: "I need a new cheque book with 25 leaves", color: "qa-orange" },
  { label: "Update address", message: "I would like to update my registered address", color: "qa-pink" },
];

function App() {
  const [auth, setAuth] = useState(null); // { token, customerId, name } | null
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hi, I'm here to help with your account. Ask me anything, or use a quick action on the left." },
  ]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleLogin({ token, customerId, name }) {
    setAuth({ token, customerId, name });
  }

  function handleLogout() {
    setAuth(null);
    setMessages([
      { sender: "bot", text: "Hi, I'm here to help with your account. Ask me anything, or use a quick action on the left." },
    ]);
  }

  async function sendMessage(overrideText) {
    const text = (overrideText ?? input).trim();
    if (!text || isSending || !auth) return;

    setMessages((prev) => [...prev, { sender: "user", text }]);
    setInput("");
    setIsSending(true);
    setMessages((prev) => [...prev, { sender: "bot", text: "Thinking...", loading: true }]);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${auth.token}`,
        },
        body: JSON.stringify({ message: text }),
      });

      if (response.status === 401) {
        // Token expired or invalid - force back to login
        setAuth(null);
        return;
      }
      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const data = await response.json();
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = { sender: "bot", text: data.reply };
        return updated;
      });
    } catch (err) {
      console.error(err);
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          sender: "bot",
          text: "Something went wrong reaching the assistant. Please try again.",
        };
        return updated;
      });
    } finally {
      setIsSending(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter") sendMessage();
  }

  if (!auth) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <span></span><span></span><span></span><span></span>
          </div>
          <span className="brand-name">Fictional Bank</span>
        </div>

        <div className="field-group">
          <label>Signed in as</label>
          <div className="signed-in-name">{auth.name}</div>
          <button className="logout-btn" onClick={handleLogout}>
            Log out
          </button>
        </div>

        <div className="quick-actions">
          <span className="quick-actions-label">Quick actions</span>
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action.label}
              className={`quick-action-btn ${action.color}`}
              onClick={() => sendMessage(action.message)}
              disabled={isSending}
            >
              {action.label}
            </button>
          ))}
        </div>
      </aside>

      <main className="main-panel">
        <header className="main-header">
          <div>
            <h1>{auth.name}</h1>
            <span className="header-sub">Customer support assistant</span>
          </div>
          <span className="status-pill">Online</span>
        </header>

        <div className="chat-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.sender}`}>
              <div className={`bubble ${msg.loading ? "loading" : ""}`}>{msg.text}</div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input">
          <input
            type="text"
            placeholder="Ask about your account..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSending}
          />
          <button onClick={() => sendMessage()} disabled={isSending}>
            Send
          </button>
        </div>
      </main>
    </div>
  );
}

export default App;