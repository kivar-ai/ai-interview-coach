import { useEffect, useState } from "react";
import { API } from "./api";

function PlanScreen({ studentId, options }) {
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState("");

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

  if (error) return <p style={{ color: "red" }}>{error}</p>;
  if (!plan) return <p>Building your study plan...</p>;

  return (
    <div>
      <h2>Your study plan</h2>
      {plan.steps.map((step) => (
        <div key={step.order}>
          <h3>
            Step {step.order}: {step.title} <i>({skillName(step.skill)})</i>
          </h3>
          <ul>
            {step.tasks.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
          {step.resources.length > 0 && (
            <p>
              Learn from:{" "}
              {step.resources.map((r) => (
                <span key={r.url}>
                  <a href={r.url} target="_blank" rel="noreferrer">
                    {r.title}
                  </a>{" "}
                </span>
              ))}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

export default PlanScreen;