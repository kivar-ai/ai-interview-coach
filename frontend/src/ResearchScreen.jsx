import { useEffect, useState } from "react";
import { API } from "./api";

function ResearchScreen({ profile, options, onNext }) {
  const studentId = profile.studentId;
  const roleName = options.roles.find((r) => r.id === profile.role)?.name;
  const [research, setResearch] = useState(null);
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    let stopped = false;
    const started = Date.now();
    const timer = setInterval(() => setSeconds(Math.round((Date.now() - started) / 1000)), 1000);

    async function poll() {
      try {
        while (!stopped) {
          const response = await fetch(`${API}/research`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ student_id: studentId }),
          });
          const data = await response.json();
          if (!response.ok) {
            setError(data.error);
            break;
          }
          if (response.status === 200) {
            setResearch(data);
            break;
          }
          await new Promise((resolve) => setTimeout(resolve, 5000));
        }
      } catch {
        setError("The backend is not reachable.");
      }
      clearInterval(timer);
    }
    poll();

    return () => {
      stopped = true;
      clearInterval(timer);
    };
  }, [studentId]);

  const skillName = (id) => options.skills.find((s) => s.id === id)?.name || id;

  return (
    <div>
      <p>
        <b>{profile.name}</b> · {roleName} at {profile.company || "any company"}
      </p>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {!research && !error && (
        <p>Researching your job... {seconds} seconds. A new job can take a few minutes the first time.</p>
      )}
      {research && (
        <div>
          <h2>What this job needs</h2>
          <ul>
            {research.skills.map((s) => (
              <li key={s.skill}>
                {skillName(s.skill)}: {s.importance}{" "}
                {s.basis === "web" ? (
                  <span>
                    (from the web:{" "}
                    {s.sources.map((url, i) => (
                      <a key={url} href={url} target="_blank" rel="noreferrer">source {i + 1} </a>
                    ))}
                    )
                  </span>
                ) : (
                  <span>(from our role profile)</span>
                )}
              </li>
            ))}
          </ul>
          {research.warnings.map((w) => <p key={w}>{w}</p>)}
          <button onClick={onNext}>Start the test</button>
        </div>
      )}
    </div>
  );
}

export default ResearchScreen;