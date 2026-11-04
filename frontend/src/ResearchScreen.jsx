import { useEffect, useState } from "react";
import { API } from "./api";

const HOW = [
  ["Search the web", "for job posts that match your role and company."],
  ["Read the pages", "in full, not just the search snippets."],
  ["Pick out the skills", "each job post asks for, with the exact words as a quote."],
  ["Check every quote", "against the page. Anything we cannot prove is dropped."],
];

const GROUPS = [
  { key: "high", title: "High priority" },
  { key: "medium", title: "Medium priority" },
  { key: "low", title: "Lower priority" },
];

function host(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function clock(totalSeconds) {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function ResearchScreen({ profile, options, onNext }) {
  const studentId = profile.studentId;
  const [research, setResearch] = useState(null);
  const [working, setWorking] = useState(false);
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
          setWorking(true);
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
  const roleName = options.roles.find((r) => r.id === profile.role)?.name;
  const target = profile.company ? `${roleName} at ${profile.company}` : roleName;

  if (error) {
    return (
      <div>
        <h2>Research did not finish</h2>
        <p className="error" role="alert">{error}</p>
        <p className="lead">Check that the backend and Ollama are running, then refresh the page and try again.</p>
      </div>
    );
  }

  if (!research) {
    return (
      <div>
        <h2>Reading job posts for {target}</h2>
        <p className="lead">
          {working
            ? "This is the first time we research this job, so it takes about 3 to 5 minutes. The result is saved for next time."
            : "Checking what we already know about this job..."}
        </p>
        {working && (
          <div className="wait">
            <div className="pulse" role="timer" aria-label="Time elapsed">
              <span>{clock(seconds)}</span>
            </div>
            <div>
              <h3>What we are doing</h3>
              <ol className="how">
                {HOW.map(([lead, rest]) => (
                  <li key={lead}>
                    <strong>{lead}</strong> {rest}
                  </li>
                ))}
              </ol>
            </div>
          </div>
        )}
      </div>
    );
  }

  const proven = research.skills.filter((s) => s.basis === "web").length;

  return (
    <div>
      <h2>What {profile.company || "this role"} looks for</h2>
      <p className="lead">
        {research.skills.length} skills for {roleName}. {proven > 0
          ? `${proven} are proven by a quote from a real job post, and the rest come from our standard profile for the role.`
          : "These come from our standard profile for the role, because we could not prove any skill from the job posts we found."}
      </p>

      {research.warnings.length > 0 && (
        <div className="note">
          {research.warnings.map((w) => (
            <p key={w}>{w}</p>
          ))}
        </div>
      )}

      {GROUPS.map((g) => {
        const rows = research.skills.filter((s) => s.importance === g.key);
        if (rows.length === 0) return null;
        return (
          <section key={g.key}>
            <h3>
              {g.title} <span className="count-soft">{rows.length}</span>
            </h3>
            <div className="skill-list">
              {rows.map((s) => (
                <div className="skill" key={s.skill}>
                  <span className="skill-name">{skillName(s.skill)}</span>
                  <span className="proof">
                    {s.basis === "web" ? (
                      <>
                        <span className="tag web">Proven on the web</span>
                        {s.sources.map((url) => (
                          <a key={url} href={url} target="_blank" rel="noreferrer">
                            {host(url)}
                          </a>
                        ))}
                      </>
                    ) : (
                      <span className="tag base">Standard role profile</span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          </section>
        );
      })}

      <p className="actions">
        <button onClick={onNext}>Start the skill test</button>
      </p>
      <p className="hint">You answer one question at a time. Grading runs in the background while you write.</p>
    </div>
  );
}

export default ResearchScreen;