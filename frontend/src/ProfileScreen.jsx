import { useState } from "react";
import { API } from "./api";

const LEVELS = [
  { value: "", label: "Skip" },
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

function ProfileScreen({ options, onSaved }) {
  const [name, setName] = useState("");
  const [role, setRole] = useState(options.roles[0].id);
  const [company, setCompany] = useState("");
  const [ratings, setRatings] = useState({});
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const rated = Object.values(ratings).filter(Boolean).length;

  function setRating(skill, level) {
    setRatings({ ...ratings, [skill]: level });
  }

  function saveProfile(event) {
    event.preventDefault();
    setError("");
    if (!name.trim()) {
      setError("Add your name to continue.");
      return;
    }
    const self_rating = {};
    for (const skill in ratings) {
      if (ratings[skill]) self_rating[skill] = ratings[skill];
    }
    setSaving(true);
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
      .catch((e) => {
        setError(e.message);
        setSaving(false);
      });
  }

  return (
    <form onSubmit={saveProfile}>
      <h2>Prepare for the job you want</h2>
      <p className="lead">
        Pick a role and a company. We read real job posts, test you on what they ask for, and show you exactly
        where to practise.
      </p>

      <div className="field">
        <label htmlFor="name">Your name</label>
        <input id="name" value={name} onChange={(e) => setName(e.target.value)} autoComplete="given-name" />
      </div>

      <fieldset className="plain">
        <legend>Target role</legend>
        <div className="tiles">
          {options.roles.map((r) => (
            <label key={r.id} className="tile">
              <input type="radio" name="role" value={r.id} checked={role === r.id} onChange={() => setRole(r.id)} />
              <span>{r.name}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="field">
        <label htmlFor="company">Company</label>
        <input id="company" value={company} onChange={(e) => setCompany(e.target.value)} placeholder="For example, Infosys" />
        <p className="hint">Optional. With a company name, we read that company's own job posts.</p>
      </div>

      <div className="skills-head">
        <h3>How would you rate yourself?</h3>
        <span className="count">
          {rated} of {options.skills.length} rated
        </span>
      </div>
      <p className="hint">Be honest. We compare this with what the test measures, and the gap is useful to you.</p>

      <div className="skills">
        {options.skills.map((s) => (
          <fieldset key={s.id} className="skill-row">
            <legend>{s.name}</legend>
            <div className="seg">
              {LEVELS.map((l) => (
                <label key={l.value || "skip"}>
                  <input
                    type="radio"
                    name={`skill-${s.id}`}
                    checked={(ratings[s.id] || "") === l.value}
                    onChange={() => setRating(s.id, l.value)}
                  />
                  <span>{l.label}</span>
                </label>
              ))}
            </div>
          </fieldset>
        ))}
      </div>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <p className="actions">
        <button type="submit" disabled={saving}>
          {saving ? "Saving..." : "Start my job research"}
        </button>
      </p>
    </form>
  );
}

export default ProfileScreen;