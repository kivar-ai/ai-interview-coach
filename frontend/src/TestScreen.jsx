import { useEffect, useState } from "react";
import { API } from "./api";

function TestScreen({ studentId, options }) {
  const [test, setTest] = useState(null);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let stopped = false;
    fetch(`${API}/test?student_id=${studentId}`)
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.error);
        return data;
      })
      .then((data) => {
        if (!stopped) setTest(data);
      })
      .catch((e) => {
        if (!stopped) setError(e.message);
      });
    return () => {
      stopped = true;
    };
  }, [studentId]);

  const skillName = (id) => options.skills.find((s) => s.id === id)?.name || id;

  function submit() {
    setError("");
    setBusy(true);
    fetch(`${API}/test/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student_id: studentId,
        test_id: test.test_id,
        question_id: test.questions[index].question_id,
        answer,
      }),
    })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.error);
        return data;
      })
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setBusy(false));
  }

  function next() {
    setResult(null);
    setAnswer("");
    setIndex(index + 1);
  }

  if (error && !test) return <p style={{ color: "red" }}>{error}</p>;
  if (!test) return <p>Preparing your test...</p>;

  const skipped = test.skipped_skills || [];

  if (index >= test.questions.length) {
    return (
      <div>
        <h2>Test finished</h2>
        <p>You answered {test.questions.length} questions. The gap report comes next.</p>
      </div>
    );
  }

  const q = test.questions[index];

  return (
    <div>
      <h2>
        Question {index + 1} of {test.questions.length}
      </h2>
      <p>
        <i>{skillName(q.skill)}</i>
      </p>
      <p>{q.text}</p>

      <textarea
        rows={6}
        cols={60}
        value={answer}
        disabled={busy || result !== null}
        onChange={(e) => setAnswer(e.target.value)}
      />
      <p>
        {result === null && (
          <button onClick={submit} disabled={busy}>
            {busy ? "Grading... (can take a minute)" : "Submit answer"}
          </button>
        )}
      </p>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {result && (
        <div>
          <p>
            <b>
              Score: {result.score} / {result.max_score}
            </b>
          </p>
          <p>{result.feedback}</p>
          {result.missed_points.length > 0 && (
            <div>
              <p>You missed:</p>
              <ul>
                {result.missed_points.map((m) => (
                  <li key={m}>{m}</li>
                ))}
              </ul>
            </div>
          )}
          <button onClick={next}>
            {index + 1 < test.questions.length ? "Next question" : "Finish"}
          </button>
        </div>
      )}

      {skipped.length > 0 && (
        <p>Not tested yet (no questions): {skipped.map(skillName).join(", ")}</p>
      )}
    </div>
  );
}

export default TestScreen;