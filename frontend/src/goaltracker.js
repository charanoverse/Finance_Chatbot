import React, { useState } from "react";
import axios from "axios";

const GoalTracker = () => {
  const [userId] = useState("user123"); // default for demo
  const [goal, setGoal] = useState("");
  const [targetAmount, setTargetAmount] = useState("");
  const [durationMonths, setDurationMonths] = useState("");
  const [saveAmount, setSaveAmount] = useState("");
  const [status, setStatus] = useState(null);

  // Create Goal
  const handleSetGoal = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post("http://localhost:8000/goal", {
        user_id: userId,
        goal,
        target_amount: Number(targetAmount),
        duration_months: Number(durationMonths),
      });
      setStatus(res.data);
      alert("Goal set successfully ✅");
    } catch (err) {
      console.error(err);
    }
  };

  // Save Money
  const handleSaveMoney = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post("http://localhost:8000/goal/save", {
        user_id: userId,
        amount: Number(saveAmount),
      });
      setStatus(res.data);
      alert("Saving added 💰");
    } catch (err) {
      console.error(err);
    }
  };

  // Get Status
  const fetchStatus = async () => {
    try {
      const res = await axios.get(
        `http://localhost:8000/goal/status/${userId}`
      );
      setStatus(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-6 max-w-xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Financial Goal Tracker</h2>

      {/* Set Goal Form */}
      <form onSubmit={handleSetGoal} className="mb-6 space-y-2">
        <input
          type="text"
          placeholder="Goal (e.g., Buy a bike)"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          className="border p-2 w-full"
        />
        <input
          type="number"
          placeholder="Target Amount"
          value={targetAmount}
          onChange={(e) => setTargetAmount(e.target.value)}
          className="border p-2 w-full"
        />
        <input
          type="number"
          placeholder="Duration (Months)"
          value={durationMonths}
          onChange={(e) => setDurationMonths(e.target.value)}
          className="border p-2 w-full"
        />
        <button type="submit" className="bg-blue-500 text-white px-4 py-2 rounded">
          Set Goal
        </button>
      </form>

      {/* Add Saving Form */}
      <form onSubmit={handleSaveMoney} className="mb-6 space-y-2">
        <input
          type="number"
          placeholder="Amount to Save"
          value={saveAmount}
          onChange={(e) => setSaveAmount(e.target.value)}
          className="border p-2 w-full"
        />
        <button type="submit" className="bg-green-500 text-white px-4 py-2 rounded">
          Add Saving
        </button>
      </form>

      {/* Fetch Status */}
      <button
        onClick={fetchStatus}
        className="bg-gray-600 text-white px-4 py-2 rounded mb-4"
      >
        Check Progress
      </button>

      {/* Status Display */}
      {status && (
        <div className="border p-4 rounded bg-gray-50">
          <h3 className="text-lg font-semibold mb-2">Goal Progress</h3>
          {status.error ? (
            <p className="text-red-500">{status.error}</p>
          ) : (
            <>
              <p>🎯 Goal: {status.goal}</p>
              <p>💰 Target: ₹{status.target}</p>
              <p>✅ Saved: ₹{status.saved}</p>
              <p>📉 Remaining: ₹{status.remaining}</p>
              <p>📊 Progress: {status.progress_percent}%</p>
              <p>📆 Months Left: {status.months_left}</p>

              {/* Progress Bar */}
              <div className="w-full bg-gray-300 rounded h-4 mt-2">
                <div
                  className="bg-green-500 h-4 rounded"
                  style={{ width: `${status.progress_percent}%` }}
                ></div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default GoalTracker;
