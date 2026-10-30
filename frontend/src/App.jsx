import { useEffect, useState } from "react";
import { API } from "./api";
import ProfileScreen from "./ProfileScreen";
import ResearchScreen from "./ResearchScreen";
import TestScreen from "./TestScreen";
import ReportScreen from "./ReportScreen";
import PlanScreen from "./PlanScreen";

function App() {
  const [options, setOptions] = useState(null);
  const [screen, setScreen] = useState("profile");
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    fetch(`${API}/options`)
      .then((response) => response.json())
      .then(setOptions)
      .catch(() => setOptions({ error: true }));
  }, []);

  if (options === null) return <p>Loading...</p>;
  if (options.error) return <p>The backend is not reachable.</p>;

  return (
    <div>
      <h1>AI Interview Coach</h1>
      {screen === "profile" && (
        <ProfileScreen
          options={options}
          onSaved={(p) => {
            setProfile(p);
            setScreen("research");
          }}
        />
      )}
      {screen === "research" && (
        <ResearchScreen profile={profile} options={options} onNext={() => setScreen("test")} />
      )}
      {screen === "test" && (
        <TestScreen studentId={profile.studentId} options={options} onDone={() => setScreen("report")} />
      )}
      {screen === "report" && (
        <ReportScreen studentId={profile.studentId} options={options} onNext={() => setScreen("plan")} />
      )}
      {screen === "plan" && <PlanScreen studentId={profile.studentId} options={options} />}
    </div>
  );
}

export default App;