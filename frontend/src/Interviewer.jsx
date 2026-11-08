import { useEffect, useState } from "react";

const synth = typeof window !== "undefined" ? window.speechSynthesis : undefined;

function pickVoice() {
  if (!synth) return null;
  const voices = synth.getVoices();
  return (
    voices.find((v) => /^en/i.test(v.lang) && /natural|online/i.test(v.name)) ||
    voices.find((v) => /^en[-_]IN/i.test(v.lang)) ||
    voices.find((v) => /^en/i.test(v.lang)) ||
    null
  );
}

function Face({ speaking }) {
  return (
    <svg viewBox="0 0 200 200" role="img" aria-label="Your interviewer" className={`face ${speaking ? "speaking" : ""}`}>
      <circle cx="100" cy="100" r="100" fill="#e3f1eb" />
      {/* shoulders and collar */}
      <path d="M22 200 C22 152 66 140 100 140 C134 140 178 152 178 200 Z" fill="#0a4d3a" />
      <path d="M84 141 L100 166 L116 141 Z" fill="#ffc93c" />
      {/* neck and head */}
      <rect x="88" y="108" width="24" height="38" rx="11" fill="#c98e5f" />
      <circle cx="62" cy="94" r="7" fill="#d79a68" />
      <circle cx="138" cy="94" r="7" fill="#d79a68" />
      <ellipse cx="100" cy="90" rx="38" ry="44" fill="#e0a577" />
      {/* hair */}
      <path d="M59 90 C52 46 88 32 112 37 C142 42 150 66 141 92 C134 70 120 60 100 60 C82 60 66 70 59 90 Z" fill="#2a1f1a" />
      {/* eyes and brows */}
      <g className="eyes">
        <ellipse cx="84" cy="92" rx="4.6" ry="5.6" fill="#182024" />
        <ellipse cx="116" cy="92" rx="4.6" ry="5.6" fill="#182024" />
      </g>
      <path d="M74 80 Q84 74 94 79" stroke="#2a1f1a" strokeWidth="3" fill="none" strokeLinecap="round" />
      <path d="M106 79 Q116 74 126 80" stroke="#2a1f1a" strokeWidth="3" fill="none" strokeLinecap="round" />
      {/* cheeks, nose */}
      <circle cx="74" cy="106" r="7" fill="#e58a7a" opacity="0.35" />
      <circle cx="126" cy="106" r="7" fill="#e58a7a" opacity="0.35" />
      <path d="M100 96 Q95 106 101 108" stroke="#b9774c" strokeWidth="2.5" fill="none" strokeLinecap="round" />
      {/* mouth */}
      {speaking ? (
        <ellipse className="mouth" cx="100" cy="119" rx="10" ry="8" fill="#7a2e2a" />
      ) : (
        <path d="M87 115 Q100 128 113 115" stroke="#7a2e2a" strokeWidth="3.5" fill="none" strokeLinecap="round" />
      )}
    </svg>
  );
}

// The interviewer: a face, a speech bubble with the question, and (when the browser can talk) a voice.
function Interviewer({ text, skill }) {
  const canSpeak = !!synth && typeof SpeechSynthesisUtterance !== "undefined";
  const [muted, setMuted] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [replays, setReplays] = useState(0);

  useEffect(() => {
    if (!canSpeak || muted) return;
    let timer = setTimeout(() => {
      synth.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      const voice = pickVoice();
      if (voice) utterance.voice = voice;
      utterance.rate = 0.95;
      utterance.onstart = () => setSpeaking(true);
      utterance.onend = () => setSpeaking(false);
      utterance.onerror = () => setSpeaking(false);
      synth.speak(utterance);
    }, 200);
    return () => {
      clearTimeout(timer);
      synth.cancel();
      setSpeaking(false);
    };
  }, [text, muted, replays, canSpeak]);

  return (
    <div className="interviewer">
      <div className={`avatar ${speaking ? "speaking" : ""}`}>
        <Face speaking={speaking} />
      </div>
      <div className="bubble">
        <span className="who">Your interviewer asks{skill ? ` · ${skill}` : ""}</span>
        <p className="q" aria-live="polite">{text}</p>
        {canSpeak && (
          <div className="voice">
            <button type="button" className="btn-quiet small" onClick={() => setReplays(replays + 1)} disabled={muted}>
              Replay question
            </button>
            <button type="button" className="btn-quiet small" onClick={() => setMuted(!muted)} aria-pressed={muted}>
              {muted ? "Turn voice on" : "Mute voice"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Interviewer;
