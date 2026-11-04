import { useEffect, useState } from "react";
import { API } from "./api";

function TestScreen({ studentId, options, onDone, practice = false }) {
  const [test, setTest] = useState(null);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [results, setResults] = useState(null);

  useEffect(() => {
    let stopped = false;
    fetch(`${API}/${practice ? "practice" : "test"}?student_id=${studentId}`)
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
  }, [studentId, practice]);

  const finishedAnswering = test !== null && index >= test.questions.length;

  // After the last answer: ask for progress every 5 seconds until everything is graded.
  useEffect(() => {
    if (!finishedAnswering) return;
    let stopped = false;
    async function poll() {
      while (!stopped) {
        try {
          const response = await fetch(
            `${API}/test/results?student_id=${studentId}&test_id=${test.test_id}`
          );
          const data = await response.json();
          if (!response.ok) throw new Error(data.error);
          if (stopped) return;
          setResults(data);
          if (data.finished) return;
        } catch (e) {
          if (!stopped) setError(e.message);
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, 5000));
      }
    }
    poll();
    return () => {
      stopped = true;
    };
  }, [finishedAnswering, studentId, test]);

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
      })
      .then(() => {
        setAnswer("");
        setIndex(index + 1);
      })
      .catch((e) => setError(e.message))
      .finally(() => setBusy(false));
  }

  if (error && !test) return <p style={{ color: "red" }}>{error}</p>;
  if (!test) return <p>Preparing your test...</p>;

  if (finishedAnswering) {
    return (
      <div>
        <h2>Your results</h2>
        {error && <p style={{ color: "red" }}>{error}</p>}
        {!results && <p>Checking...</p>}
        {results && !results.finished && (
          <p>
            Graded {results.graded} of {results.total} answers. Each one takes about a minute, please wait...
          </p>
        )}
        {results &&
          results.questions.map((q) => (
            <div key={q.question_id}>
              <h3>
                {q.number}. {q.text} <i>({skillName(q.skill)})</i>
              </h3>
              {q.status === "done" && (
                <div>
                  <p>
                    <b>
                      Score: {q.score} / {q.max_score}
                    </b>
                  </p>
                  <p>{q.feedback}</p>
                  {q.missed_points.length > 0 && (
                    <ul>
                      {q.missed_points.map((m) => (
                        <li key={m}>{m}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
              {q.status === "failed" && (
                <p style={{ color: "red" }}>This answer could not be graded. {q.feedback}</p>
              )}
              {(q.status === "pending" || q.status === "unanswered") && <p>Waiting to be graded...</p>}
            </div>
          ))}
        {results && results.finished && (
          <button onClick={onDone}>
            {practice ? "See my updated gap report" : "See my gap report"}
          </button>
        )}
      </div>
    );
  }

  const q = test.questions[index];
  const skipped = test.skipped_skills || [];

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
        disabled={busy}
        onChange={(e) => setAnswer(e.target.value)}
      />
      <p>
        <button onClick={submit} disabled={busy}>
          {busy ? "Saving..." : index + 1 < test.questions.length ? "Submit and next" : "Submit last answer"}
        </button>
      </p>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {skipped.length > 0 && (
        <p>Not tested yet (no questions): {skipped.map(skillName).join(", ")}</p>
      )}
    </div>
  );
}

export default TestScreen;