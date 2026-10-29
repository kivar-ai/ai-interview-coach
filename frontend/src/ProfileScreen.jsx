import { useState } from "react";
import { API } from "./api";

function ProfileScreen({ options, onSaved }) {
  const [name, setName] = useState("");
  const [role, setRole] = useState(options.roles[0].id);
  const [company, setCompany] = useState("");
  const [ratings, setRatings] = useState({});
  const [error, setError] = useState("");

  function setRating(skill, level) {
    setRatings({ ...ratings, [skill]: level });
  }

  function saveProfile() {
    setError("");
    if (!name.trim()) {
      setError("Please type your name.");
      return;
    }
    const self_rating = {};
    for (const skill in ratings) {
      if (ratings[skill]) self_rating[skill] = ratings[skill];
    }
    fetch(`${API}/profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, target_role: role, company: company || null, self_rating }),
    })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.error);
        return data;
      })
      .then((data) => onSaved({ studentId: data.student_id, name, role, company }))
      .catch((e) => setError(e.message));
  }

  return (
    <div>
      <h2>Tell us about you</h2>
      <p>
        <label>
          Your name: <input value={name} onChange={(e) => setName(e.target.value)} />
        </label>
      </p>
      <p>
        <label>
          Target role:{" "}
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            {options.roles.map((r) => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>
        </label>
      </p>
      <p>
        <label>
          Company (optional): <input value={company} onChange={(e) => setCompany(e.target.value)} />
        </label>
      </p>

      <h3>How would you rate yourself?</h3>
      {options.skills.map((s) => (
        <p key={s.id}>
          <label>
            {s.name}:{" "}
            <select value={ratings[s.id] || ""} onChange={(e) => setRating(s.id, e.target.value)}>
              <option value="">not rated</option>
              <option value="beginner">beginner</option>
              <option value="intermediate">intermediate</option>
              <option value="advanced">advanced</option>
            </select>
          </label>
        </p>
      ))}

      <button onClick={saveProfile}>Save and continue</button>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}

export default ProfileScreen;