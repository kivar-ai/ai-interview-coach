import { useEffect, useState } from "react";
import { API } from "./api";

function ReportScreen({ studentId, options, onNext }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let stopped = false;
    fetch(`${API}/report?student_id=${studentId}`)
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.error);
        return data;
      })
      .then((data) => {
        if (!stopped) setReport(data);
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
  if (!report) return <p>Building your report...</p>;

  return (
    <div>
      <h2>Your gap report</h2>

      <h3>Your biggest gaps</h3>
      {report.top_gaps.length === 0 ? (
        <p>No gaps found.</p>
      ) : (
        <ol>
          {report.top_gaps.map((id) => (
            <li key={id}>{skillName(id)}</li>
          ))}
        </ol>
      )}

      <h3>All skills</h3>
      <table border="1" cellPadding="6" style={{ margin: "0 auto" }}>
        <thead>
          <tr>
            <th>Skill</th>
            <th>Job needs</th>
            <th>You said</th>
            <th>Measured</th>
            <th>Gap</th>
          </tr>
        </thead>
        <tbody>
          {report.skills.map((s) => (
            <tr key={s.skill}>
              <td>{skillName(s.skill)}</td>
              <td>{s.job_needs}</td>
              <td>{s.self_rating || "not rated"}</td>
              <td>{s.measured_score === null ? "not tested" : `${s.measured_score}%`}</td>
              <td>{s.gap === null ? "-" : s.gap}</td>
            </tr>
          ))}
        </tbody>
      </table>
            <p>
        <button onClick={onNext}>See my study plan</button>
      </p>
    </div>
  );
}

export default ReportScreen;