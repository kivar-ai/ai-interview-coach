const STEPS = [
  { id: "profile", label: "Your profile" },
  { id: "research", label: "Job research" },
  { id: "test", label: "Skill test" },
  { id: "report", label: "Gap report" },
  { id: "plan", label: "Study plan" },
  { id: "practice", label: "Practice round" },
];

function Shell({ screen, profile, roleName, children }) {
  const current = STEPS.findIndex((s) => s.id === screen);
  return (
    <div className="shell">
      <aside className="rail">
        <div className="brand">
          <svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true">
            <circle cx="16" cy="16" r="12" fill="none" stroke="#ffc93c" strokeWidth="3" />
            <circle cx="16" cy="16" r="4.5" fill="#ffc93c" />
          </svg>
          <span>Interview Coach</span>
        </div>

        <ol className="steps">
          {STEPS.map((s, i) => (
            <li
              key={s.id}
              className={i < current ? "done" : i === current ? "current" : ""}
              aria-current={i === current ? "step" : undefined}
            >
              <span className="dot" aria-hidden="true" />
              <span className="step-label">{s.label}</span>
            </li>
          ))}
        </ol>

        {profile && (
          <div className="who">
            <strong>{profile.name}</strong>
            <span>
              {roleName}
              {profile.company ? ` at ${profile.company}` : ""}
            </span>
          </div>
        )}
      </aside>

      <main className="main">
        <div className="page">{children}</div>
      </main>
    </div>
  );
}

export default Shell;