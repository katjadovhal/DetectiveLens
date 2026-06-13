import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { WelcomePage } from './routes/onboarding/WelcomePage';
import { HomePage } from './routes/home/HomePage';
import { FakePostChallengePage } from './routes/challenges/FakePostChallengePage';
import { PlaceholderPage } from './routes/PlaceholderPage';

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/onboarding/welcome" element={<WelcomePage />} />
        <Route path="/" element={<HomePage />} />
        <Route path="/challenges/fake-post/:id" element={<FakePostChallengePage />} />
        <Route
          path="/progress/xp"
          element={
            <PlaceholderPage
              title="XP & Levels"
              description="Track your detective rank and points. Coming in Sprint 3."
            />
          }
        />
        <Route
          path="/profile"
          element={
            <PlaceholderPage
              title="Profile"
              description="Customize your avatar and display name. Coming in Sprint 3."
            />
          }
        />
        <Route
          path="/profile/statistics"
          element={
            <PlaceholderPage
              title="Statistics"
              description="View your total XP, challenges played, and accuracy. Coming in Sprint 3."
            />
          }
        />
        <Route
          path="/profile/settings"
          element={
            <PlaceholderPage
              title="Settings"
              description="Notifications, sound, and privacy controls. Coming in Sprint 3."
            />
          }
        />
        <Route
          path="/profile/help"
          element={
            <PlaceholderPage
              title="Help & Support"
              description="FAQ, contact, and feedback. Coming in Sprint 3."
            />
          }
        />
        <Route path="*" element={<Navigate to="/onboarding/welcome" replace />} />
      </Route>
    </Routes>
  );
}
