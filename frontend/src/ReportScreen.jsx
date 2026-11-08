import { useEffect, useState } from "react";
import { API } from "./api";

// Where the "what you said" marker is drawn on the 0 to 100 track. Drawing only.
const SELF_POSITION = { beginner: 25, intermediate: 55, advanced: 85 };
const NEED_LABEL = { high: "High need", medium: "Medium need", low: "Low need" };

function clamp(n) {
  return Math.max(0, Math.min(100, n));
}

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

  if (error) {
    return (
      <div>
        <h2>The report could not be built</h2>
        <p className="error" role="alert">{error}</p>
        <p className="lead">Check that the backend is running, then refresh the page.</p>
      </div>
    );
  }
  if (!report) {
    return (
      <div>
        <h2>Building your report</h2>
        <p className="lead">One moment...</p>
      </div>
    );
  }

  // Biggest gap first. Skills we could not test go to the end.
  const mapRows = [...report.skills].sort((a, b) => (b.gap ?? -1) - (a.gap ?? -1));
  const topRows = report.top_gaps
    .map((id) => report.skills.find((s) => s.skill === id))
    .filter(Boolean);

  function story(s) {
    const said = s.self_rating ? `You rated yourself ${s.self_rating}. ` : "";
    return `${said}Your answers scored ${s.measured_score}%.`;
  }

  return (
    <div>
      <h2>Your gap report</h2>
      <p className="lead">
        Each bar shows what your answers scored. The yellow part is the gap still to close for this job.
      </p>

      <section aria-label="Gap map" className="gapmap">
        <ul className="legend">
          <li><i className="sw got" />Your score</li>
          <li><i className="sw gap" />Gap to close</li>
          <li><i className="sw said" />What you said</li>
        </ul>

        {mapRows.map((s) => {
          const measured = s.measured_score === null ? null : clamp(s.measured_score);
          const gap = s.gap === null || s.gap <= 0 ? 0 : s.gap;
          return (
            <div className="gm-row" key={s.skill}>
              <div className="gm-name">
                <strong>{skillName(s.skill)}</strong>
                <span className={`need ${s.job_needs}`}>{NEED_LABEL[s.job_needs] || s.job_needs}</span>
              </div>

              <div
                className={`track ${measured === null ? "untested" : ""}`}
                role="img"
                aria-label={
                  measured === null
                    ? `${skillName(s.skill)}: not tested`
                    : `${skillName(s.skill)}: scored ${measured} percent, gap ${gap}`
                }
              >
                {measured !== null && (
                  <>
                    <span className="got" style={{ width: `${measured}%` }} />
                    {gap > 0 && (
                      <span className="gap" style={{ left: `${measured}%`, width: `${clamp(measured + gap) - measured}%` }} />
                    )}
                  </>
                )}
                {SELF_POSITION[s.self_rating] && (
                  <span className="said" style={{ left: `${SELF_POSITION[s.self_rating]}%` }} title={`You said: ${s.self_rating}`} />
                )}
              </div>

              <div className="gm-num">
                {measured === null ? (
                  <span className="muted">Not tested</span>
                ) : (
                  <>
                    <strong>{measured}%</strong>
                    <span className="muted">{gap > 0 ? `gap ${gap}` : "on target"}</span>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </section>

      <h3>Your biggest gaps</h3>
      {topRows.length === 0 ? (
        <p>No gaps found.</p>
      ) : (
        <div className="top-gaps">
          {topRows.map((s, i) => (
            <article className="callout" key={s.skill}>
              <span className="rank">{i + 1}</span>
              <div>
                <strong>{skillName(s.skill)}</strong>
                <p>{s.measured_score === null ? "Not tested yet." : story(s)}</p>
              </div>
            </article>
          ))}
        </div>
      )}

      <h3>All numbers</h3>
      <div className="table-wrap">
      <table>
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
      </div>

      <p className="actions">
        <button onClick={onNext}>See my study plan</button>
      </p>
    </div>
  );
}

export default ReportScreen;
