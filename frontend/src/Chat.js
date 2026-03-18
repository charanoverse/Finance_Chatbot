import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { Pie } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip } from "chart.js";
import { v4 as uuidv4 } from "uuid";

ChartJS.register(ArcElement, Tooltip);

const Chat = () => {
  /* ================= THEME ================= */
  const [darkMode, setDarkMode] = useState(true);

  /* ================= CHAT ================= */
  const [chatHistory, setChatHistory] = useState([
    {
      sender: "bot",
      message: "Hello 👋 I'm FinPal, your financial assistant. Ask me anything about finance!",
      options: [],
    },
  ]);
  const [userInput, setUserInput] = useState("");
  const [botTyping, setBotTyping] = useState(false);
  const chatRef = useRef(null);

  // Session ID for context tracking
  const [sessionId] = useState(() => uuidv4());

  /* ================= GOALS ================= */
  const [user] = useState("guest");
  const [goals, setGoals] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [goalForm, setGoalForm] = useState({
    goal_name: "",
    target_amount: "",
    duration_months: "",
    salary: "",
  });
  const [monthlyInput, setMonthlyInput] = useState({});

  /* ================= AUTO SCROLL ================= */
  useEffect(() => {
    if (!botTyping && chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [chatHistory, botTyping]);

  /* ================= BOT MESSAGE ================= */
  const addBotMessage = (message, options = []) => {
    setBotTyping(true);
    let i = 0;
    const msg = { sender: "bot", message: "", options };
    setChatHistory((p) => [...p, msg]);

    const interval = setInterval(() => {
      i++;
      setChatHistory((p) => {
        const copy = [...p];
        copy[copy.length - 1].message = message.slice(0, i);
        return copy;
      });
      if (i >= message.length) {
        clearInterval(interval);
        setBotTyping(false);
      }
    }, 18);
  };

  const addUserMessage = (m) =>
    setChatHistory((p) => [...p, { sender: "user", message: m }]);

  /* ================= CHAT FLOW ================= */
  const sendQuery = async () => {
    if (!userInput || botTyping) return;
    addUserMessage(userInput);
    try {
      const res = await axios.post("http://localhost:8000/chat", {
        query: userInput,
        profile: {},  // Empty profile - intent-driven mode
        session_id: sessionId,  // Session ID for context tracking
      });
      addBotMessage(res.data.answer);
    } catch {
      addBotMessage("Unable to reach the server right now.");
    }
    setUserInput("");
  };

  const handleOptionClick = async (opt) => {
    if (botTyping) return;
    addUserMessage(opt);

    // Treat option clicks as queries
    try {
      const res = await axios.post("http://localhost:8000/chat", {
        query: opt,
        profile: {},
        session_id: sessionId,  // Session ID for context tracking
      });
      addBotMessage(res.data.answer);
    } catch {
      addBotMessage("Unable to reach the server right now.");
    }
  };

  /* ================= GOAL APIs ================= */
  const fetchGoals = async () => {
    const res = await axios.get(`http://localhost:8000/goal/${user}`);
    setGoals(res.data);
  };

  useEffect(() => {
    fetchGoals();
  }, []);

  const createGoal = async () => {
    await axios.post("http://localhost:8000/goal", {
      user,
      ...goalForm,
      target_amount: +goalForm.target_amount,
      duration_months: +goalForm.duration_months,
      salary: +goalForm.salary,
    });
    setGoalForm({
      goal_name: "",
      target_amount: "",
      duration_months: "",
      salary: "",
    });
    setShowForm(false);
    fetchGoals();
  };

  const saveProgress = async (g, amt) => {
    if (!amt) return;
    await axios.post("http://localhost:8000/goal/save", {
      user,
      goal_id: g._id,
      amount_saved: Number(amt),
    });
    setMonthlyInput({ ...monthlyInput, [g._id]: "" });
    fetchGoals();
  };

  const activeGoals = goals.filter(
    (g) => g.saved_amount < g.target_amount
  );
  const completedGoals = goals.filter(
    (g) => g.saved_amount >= g.target_amount
  );

  const theme = darkMode ? dark : light;

  /* ================= UI ================= */
  return (
    <div style={{ ...theme.page }}>
      {/* NAVBAR */}
      <div style={theme.nav}>
        <strong>FinPal</strong>
        <button
          style={theme.toggle}
          onClick={() => setDarkMode(!darkMode)}
        >
          {darkMode ? "☀ Light" : "🌙 Dark"}
        </button>
      </div>

      <div style={theme.main}>
        {/* CHAT */}
        <div style={theme.chat}>
          <div style={theme.chatHeader}>🤖 FinPal Assistant</div>

          <div style={theme.chatBody} ref={chatRef}>
            {chatHistory.map((c, i) => (
              <div
                key={i}
                style={c.sender === "bot" ? theme.bot : theme.user}
              >
                {c.message}
                <div>
                  {c.options?.map((o) => (
                    <button
                      key={o}
                      onClick={() => handleOptionClick(o)}
                      style={theme.pill}
                    >
                      {o}
                    </button>
                  ))}
                </div>
              </div>
            ))}
            {botTyping && (
              <div style={theme.botMuted}>FinPal is typing…</div>
            )}
          </div>

          <div style={theme.chatInput}>
            <input
              style={theme.input}
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendQuery()}
              placeholder="Ask me anything about finance..."
            />
            <button
              style={theme.primaryBtn}
              onClick={sendQuery}
            >
              Send
            </button>
          </div>
        </div>

        {/* GOALS */}
        <div style={theme.goals}>
          <h3>🎯 Goals</h3>

          <div style={theme.summary}>
            <div>Total: {goals.length}</div>
            <div>Active: {activeGoals.length}</div>
            <div>Done: {completedGoals.length}</div>
          </div>

          <button
            style={theme.secondaryBtn}
            onClick={() => setShowForm(!showForm)}
          >
            {showForm ? "Close" : "Create Goal"}
          </button>

          {showForm && (
            <div style={theme.card}>
              {Object.keys(goalForm).map((k) => (
                <input
                  key={k}
                  style={theme.input}
                  placeholder={k.replace("_", " ")}
                  value={goalForm[k]}
                  onChange={(e) =>
                    setGoalForm({ ...goalForm, [k]: e.target.value })
                  }
                />
              ))}
              <button style={theme.primaryBtn} onClick={createGoal}>
                Save Goal
              </button>
            </div>
          )}

          {activeGoals.map((g) => {
            const pct = Math.min(
              (g.saved_amount / g.target_amount) * 100,
              100
            );
            return (
              <div key={g._id} style={theme.card}>
                <strong>{g.goal_name}</strong>
                <div style={theme.subText}>
                  ₹{g.saved_amount} / ₹{g.target_amount}
                </div>

                <Pie
                  data={{
                    labels: ["Saved", "Remaining"],
                    datasets: [
                      {
                        data: [
                          g.saved_amount,
                          g.target_amount - g.saved_amount,
                        ],
                        backgroundColor: ["#3b82f6", "#1e293b"],
                      },
                    ],
                  }}
                />

                <div style={theme.progressBar}>
                  <div
                    style={{
                      ...theme.progressFill,
                      width: `${pct}%`,
                    }}
                  />
                </div>

                <div style={theme.subText}>{pct.toFixed(2)}%</div>

                <input
                  style={theme.input}
                  placeholder="Add savings"
                  value={monthlyInput[g._id] || ""}
                  onChange={(e) =>
                    setMonthlyInput({
                      ...monthlyInput,
                      [g._id]: e.target.value,
                    })
                  }
                />

                <button
                  style={theme.primaryBtn}
                  onClick={() =>
                    saveProgress(g, monthlyInput[g._id])
                  }
                >
                  Update
                </button>
              </div>
            );
          })}

          {completedGoals.length > 0 && (
            <>
              <h4>Completed</h4>
              {completedGoals.map((g) => (
                <div
                  key={g._id}
                  style={{ ...theme.card, opacity: 0.6 }}
                >
                  ✔ {g.goal_name}
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

/* ================= THEMES ================= */
const light = {
  page: {
    background: "#F5F7FA",
    minHeight: "100vh",
    color: "#0F172A",
    fontFamily: "Inter, system-ui, sans-serif",
  },

  nav: {
    height: 64,
    background: "#FFFFFF",
    padding: "0 24px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
  },

  toggle: {
    background: "#E5E7EB",
    color: "#0F172A",
    border: "none",
    padding: "6px 12px",
    borderRadius: 8,
    cursor: "pointer",
  },

  main: {
    display: "flex",
    gap: 24,
    padding: 24,
    height: "calc(100vh - 64px)",
  },

  chat: {
    flex: 2,
    background: "#FFFFFF",
    borderRadius: 16,
    display: "flex",
    flexDirection: "column",
    boxShadow: "0 8px 24px rgba(0,0,0,0.06)",
  },

  chatHeader: {
    padding: 16,
    borderBottom: "1px solid #E5E7EB",
    fontWeight: 600,
  },

  chatBody: {
    flex: 1,
    padding: 16,
    overflowY: "auto",
    background: "#F8FAFC",
  },

  chatInput: {
    display: "flex",
    gap: 12,
    padding: 16,
    borderTop: "1px solid #E5E7EB",
    background: "#FFFFFF",
  },

  bot: {
    background: "#FFFFFF",
    padding: 12,
    borderRadius: 12,
    marginBottom: 12,
    maxWidth: "70%",
    boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
  },

  botMuted: {
    background: "#F1F5F9",
    color: "#64748B",
    padding: 10,
    borderRadius: 12,
    maxWidth: "60%",
    marginBottom: 12,
  },

  user: {
    background: "#2563EB",
    color: "#FFFFFF",
    padding: 12,
    borderRadius: 12,
    marginBottom: 12,
    marginLeft: "auto",
    maxWidth: "70%",
  },

  pill: {
    marginTop: 8,
    marginRight: 8,
    padding: "6px 14px",
    borderRadius: 999,
    border: "1px solid #E5E7EB",
    background: "#FFFFFF",
    color: "#0F172A",
    cursor: "pointer",
  },

  goals: {
    flex: 1,
    background: "#FFFFFF",
    borderRadius: 16,
    padding: 16,
    overflowY: "auto",
    boxShadow: "0 8px 24px rgba(0,0,0,0.06)",
  },

  summary: {
    display: "flex",
    justifyContent: "space-between",
    marginBottom: 12,
    padding: 12,
    borderRadius: 10,
    background: "#F8FAFC",
    color: "#475569",
    fontSize: 14,
  },

  card: {
    background: "#FFFFFF",
    padding: 16,
    borderRadius: 12,
    marginTop: 16,
    boxShadow: "0 4px 14px rgba(0,0,0,0.06)",
  },

  input: {
    width: "100%",
    padding: 10,
    borderRadius: 8,
    border: "1px solid #CBD5E1",
    background: "#FFFFFF",
    color: "#0F172A",
    marginTop: 8,
  },

  primaryBtn: {
    background: "#2563EB",
    color: "#FFFFFF",
    border: "none",
    padding: "10px 16px",
    borderRadius: 8,
    marginTop: 8,
    cursor: "pointer",
  },

  secondaryBtn: {
    background: "#E5E7EB",
    color: "#0F172A",
    border: "none",
    padding: "8px 12px",
    borderRadius: 8,
    marginTop: 8,
    cursor: "pointer",
  },

  progressBar: {
    height: 8,
    background: "#E5E7EB",
    borderRadius: 4,
    marginTop: 12,
  },

  progressFill: {
    height: "100%",
    background: "#2563EB",
    borderRadius: 4,
  },

  subText: {
    fontSize: 12,
    color: "#64748B",
    marginTop: 4,
  },
};

const dark = {
  page: {
    background: "#0f172a",
    minHeight: "100vh",
    color: "#e5e7eb",
    fontFamily: "Inter, system-ui, sans-serif",
  },
  nav: {
    height: 64,
    background: "#020617",
    padding: "0 24px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  toggle: {
    background: "#1e293b",
    color: "#e5e7eb",
    border: "none",
    padding: "6px 12px",
    borderRadius: 8,
    cursor: "pointer",
  },
  main: {
    display: "flex",
    gap: 24,
    padding: 24,
    height: "calc(100vh - 64px)",
  },
  chat: {
    flex: 2,
    background: "#020617",
    borderRadius: 16,
    display: "flex",
    flexDirection: "column",
  },
  chatHeader: {
    padding: 16,
    borderBottom: "1px solid #1e293b",
  },
  chatBody: {
    flex: 1,
    padding: 16,
    overflowY: "auto",
    background: "#020617",
  },
  chatInput: {
    display: "flex",
    gap: 12,
    padding: 16,
    borderTop: "1px solid #1e293b",
  },
  goals: {
    flex: 1,
    background: "#020617",
    borderRadius: 16,
    padding: 16,
    overflowY: "auto",
  },
  bot: {
    background: "#020617",
    border: "1px solid #1e293b",
    padding: 12,
    borderRadius: 12,
    marginBottom: 12,
    maxWidth: "70%",
  },
  botMuted: {
    color: "#94a3b8",
    marginBottom: 12,
  },
  user: {
    background: "#3b82f6",
    padding: 12,
    borderRadius: 12,
    marginBottom: 12,
    marginLeft: "auto",
    maxWidth: "70%",
  },
  pill: {
    marginTop: 8,
    marginRight: 8,
    padding: "6px 14px",
    borderRadius: 999,
    border: "1px solid #1e293b",
    background: "#020617",
    color: "#e5e7eb",
    cursor: "pointer",
  },
  card: {
    background: "#020617",
    border: "1px solid #1e293b",
    padding: 16,
    borderRadius: 12,
    marginTop: 16,
  },
  input: {
    width: "100%",
    padding: 10,
    borderRadius: 8,
    border: "1px solid #1e293b",
    background: "#020617",
    color: "#e5e7eb",
    marginTop: 8,
  },
  primaryBtn: {
    background: "#3b82f6",
    color: "#fff",
    border: "none",
    padding: "10px 16px",
    borderRadius: 8,
    marginTop: 8,
  },
  secondaryBtn: {
    background: "#1e293b",
    border: "none",
    padding: "8px 12px",
    borderRadius: 8,
    marginTop: 8,
    color: "#e5e7eb",
  },
  summary: {
    display: "flex",
    justifyContent: "space-between",
    marginBottom: 12,
    color: "#94a3b8",
  },
  progressBar: {
    height: 8,
    background: "#1e293b",
    borderRadius: 4,
    marginTop: 12,
  },
  progressFill: {
    height: "100%",
    background: "#3b82f6",
    borderRadius: 4,
  },
  subText: {
    fontSize: 12,
    color: "#94a3b8",
    marginTop: 4,
  },
};

export default Chat;
