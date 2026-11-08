import { useEffect, useState } from "react";
import { API } from "./api";
import Interviewer from "./Interviewer";

function wordCount(text) {
  const t = text.trim();
  return t === "" ? 0 : t.split(/\s+/).length;
}

function scoreClass(score, max) {
  const share = max > 0 ? score / max : 0;
  if (share >= 0.7) return "good";
  if (share >= 0.4) return "mid";
  return "low";
}

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

  if (error && !test) {
    return (
      <div>
        <h2>The test could not start</h2>
        <p className="error" role="alert">{error}</p>
        <p className="lead">Check that the backend is running, then refresh the page.</p>
      </div>
    );
  }
  if (!test) {
    return (
      <div>
        <h2>{practice ? "Picking your practice questions" : "Preparing your test"}</h2>
        <p className="lead">One moment...</p>
      </div>
    );
  }

  if (finishedAnswering) {
    const graded = results ? results.graded : 0;
    const total = results ? results.total : test.questions.length;
    const percent = total > 0 ? Math.round((graded / total) * 100) : 0;
    return (
      <div>
        <h2>{results && results.finished ? "Your results" : "Grading your answers"}</h2>
        <p className="lead">
          {results && results.finished
            ? "Every answer is marked. Open the gap report to see where you stand against the job."
            : "Each answer takes about a minute to mark. You can read the finished ones while the rest are worked on."}
        </p>

        <div className="meter" role="progressbar" aria-valuemin={0} aria-valuemax={total} aria-valuenow={graded}>
          <div className="meter-bar"><span style={{ width: `${percent}%` }} /></div>
          <span className="meter-text">{graded} of {total} marked</span>
        </div>

        {error && <p className="error" role="alert">{error}</p>}

        <div className="answers">
          {results ? (
            results.questions.map((q) => (
              <article className={`answer ${q.status}`} key={q.question_id}>
                <header>
                  <span className="qnum">{q.number}</span>
                  <span className="chip">{skillName(q.skill)}</span>
                  {q.status === "done" && (
                    <span className={`score ${scoreClass(q.score, q.max_score)}`}>
                      {q.score}<small> / {q.max_score}</small>
                    </span>
                  )}
                  {q.status === "failed" && <span className="state failed">Could not be marked</span>}
                  {(q.status === "pending" || q.status === "unanswered") && (
                    <span className="state waiting"><i className="blink" aria-hidden="true" />Marking...</span>
                  )}
                </header>
                <p className="q-text">{q.text}</p>
                {q.status === "done" && (
                  <>
                    <p className="feedback">{q.feedback}</p>
                    {q.missed_points.length > 0 && (
                      <div className="missed">
                        <strong>Add these next time</strong>
                        <ul>
                          {q.missed_points.map((m) => (
                            <li key={m}>{m}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </>
                )}
                {q.status === "failed" && <p className="error small">{q.feedback}</p>}
              </article>
            ))
          ) : (
            <p className="hint">Checking...</p>
          )}
        </div>

        {results && results.finished && (
          <p className="actions">
            <button onClick={onDone}>
              {practice ? "See my updated gap report" : "See my gap report"}
            </button>
          </p>
        )}
      </div>
    );
  }

  const q = test.questions[index];
  const skipped = test.skipped_skills || [];
  const words = wordCount(answer);
  const last = index + 1 >= test.questions.length;

  return (
    <div>
      <div className="progress" aria-label={`Question ${index + 1} of ${test.questions.length}`}>
        <ol className="pips">
          {test.questions.map((item, i) => (
            <li key={item.question_id} className={i < index ? "done" : i === index ? "now" : ""} />
          ))}
        </ol>
        <span className="progress-text">
          {practice ? "Practice" : "Question"} {index + 1} of {test.questions.length}
        </span>
      </div>

      {practice ? (
        <Interviewer text={q.text} skill={skillName(q.skill)} />
      ) : (
        <>
          <span className="chip big">{skillName(q.skill)}</span>
          <h2 className="question">{q.text}</h2>
        </>
      )}

      <div className="field">
        <label htmlFor="answer">Your answer</label>
        <textarea
          id="answer"
          rows={7}
          value={answer}
          disabled={busy}
          placeholder="Explain it in your own words, as you would to an interviewer."
          onChange={(e) => setAnswer(e.target.value)}
        />
        <div className="under">
          <span className="hint">Three to six sentences is enough. An empty answer scores 0.</span>
          <span className="hint">{words} {words === 1 ? "word" : "words"}</span>
        </div>
      </div>

      <p className="actions">
        <button onClick={submit} disabled={busy}>
          {busy ? "Saving..." : last ? "Submit last answer" : "Submit and next"}
        </button>
      </p>
      <p className="hint">Your answer is marked in the background while you move on.</p>

      {error && <p className="error" role="alert">{error}</p>}

      {skipped.length > 0 && (
        <p className="hint skipped">
          Not tested yet because we have no questions for them: {skipped.map(skillName).join(", ")}.
        </p>
      )}
    </div>
  );
}

export default TestScreen;
