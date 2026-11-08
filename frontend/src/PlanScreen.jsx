import { useEffect, useState } from "react";
import { API } from "./api";

function PlanScreen({ studentId, options, onPractice, onRestart }) {
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState("");
  const [ticked, setTicked] = useState({});

  useEffect(() => {
    let stopped = false;
    fetch(`${API}/plan?student_id=${studentId}`)
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.error);
        return data;
      })
      .then((data) => {
        if (!stopped) setPlan(data);
      })
      .catch((e) => {
        if (!stopped) setError(e.message);
      });
    return () => {
      stopped = true;
    };
  }, [studentId]);

  const skillName = (id) => options.skills.find((s) => s.id === id)?.name || id;

  if (error) {
    return (
      <div>
        <h2>The study plan could not be built</h2>
        <p className="error" role="alert">{error}</p>
        <p className="lead">Check that the backend is running, then refresh the page.</p>
      </div>
    );
  }
  if (!plan) {
    return (
      <div>
        <h2>Building your study plan</h2>
        <p className="lead">One moment...</p>
      </div>
    );
  }

  const keyOf = (step, task) => `${step.order}|${task}`;
  const allTasks = plan.steps.flatMap((step) => step.tasks.map((t) => keyOf(step, t)));
  const done = allTasks.filter((k) => ticked[k]).length;

  function toggle(key) {
    setTicked({ ...ticked, [key]: !ticked[key] });
  }

  return (
    <div>
      <h2>Your study plan</h2>
      <p className="lead">
        {plan.steps.length} {plan.steps.length === 1 ? "step" : "steps"}, in order, starting with your biggest gap.
        Every link comes from our checked list of resources.
      </p>

      {allTasks.length > 0 && (
        <p className="tasks-done" aria-live="polite">
          {done} of {allTasks.length} tasks ticked
        </p>
      )}

      <ol className="timeline">
        {plan.steps.map((step) => (
          <li key={step.order}>
            <span className="t-num">{step.order}</span>
            <div className="t-card">
              <span className="chip">{skillName(step.skill)}</span>
              <h3>{step.title}</h3>

              <ul className="checks">
                {step.tasks.map((t) => {
                  const key = keyOf(step, t);
                  return (
                    <li key={t}>
                      <label className={ticked[key] ? "ticked" : ""}>
                        <input type="checkbox" checked={!!ticked[key]} onChange={() => toggle(key)} />
                        <span>{t}</span>
                      </label>
                    </li>
                  );
                })}
              </ul>

              {step.resources.length > 0 && (
                <div className="learn">
                  <strong>Learn from</strong>
                  <div className="links">
                    {step.resources.map((r) => (
                      <a key={r.url} href={r.url} target="_blank" rel="noreferrer">
                        {r.title}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </li>
        ))}
      </ol>

      <div className="cta">
        <h3>Ready to check your progress?</h3>
        <p>A short practice round asks new questions on your biggest gaps, and your report updates.</p>
        <p className="actions">
          <button onClick={onPractice}>Start a practice round on my gaps</button>{" "}
          <button className="btn-quiet" onClick={onRestart}>Finish and start over</button>
        </p>
      </div>
    </div>
  );
}

export default PlanScreen;
