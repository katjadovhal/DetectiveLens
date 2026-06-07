import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import type { HomeDashboard } from '@detectivelens/shared';
import { api } from '../../services/api-client';
import { Card } from '../../components/ui/Card';
import { ProgressBar } from '../../components/ui/ProgressBar';
import { Button } from '../../components/ui/Button';

export function HomePage() {
  const [home, setHome] = useState<HomeDashboard | null>(null);

  useEffect(() => {
    api.getHome().then(setHome).catch(() => {});
  }, []);

  if (!home) {
    return <div className="py-20 text-center text-xl text-gray-500">Loading dashboard...</div>;
  }

  const xpMax = home.progress.totalXp + home.progress.xpToNextLevel;

  return (
    <div className="mx-auto w-full max-w-7xl space-y-10">
      <Card className="flex flex-col items-start gap-6 sm:flex-row sm:items-center">
        <div className="flex h-28 w-28 shrink-0 items-center justify-center rounded-full bg-[var(--color-lavender)] text-6xl">
          🕵️
        </div>
        <div>
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl">
            Hi, {home.greeting.displayName}!
          </h1>
          <p className="mt-2 text-2xl font-bold text-[var(--color-primary)]">{home.greeting.levelTitle}</p>
        </div>
      </Card>

      <ProgressBar current={home.progress.totalXp} max={xpMax} showLabel />

      <div className="grid gap-8 lg:grid-cols-2">
        <Card highlight className="lg:col-span-1">
          <h2 className="text-3xl font-extrabold text-[var(--color-accent-orange)]">
            {home.dailyMission.title}
          </h2>
          <p className="mt-3 text-2xl font-bold text-gray-800">{home.dailyMission.description}</p>
          <p className="mt-2 text-lg text-gray-600">+{home.dailyMission.xpBonus} Points</p>
          <Link to={`/challenges/fake-post/${home.dailyMission.challengeId}`}>
            <Button variant="secondary" className="mt-8">
              Play
            </Button>
          </Link>
        </Card>

        {home.continueLearning.challengeId && (
          <Card className="lg:col-span-1">
            <h2 className="text-2xl font-bold text-gray-800">Continue Learning</h2>
            <p className="mt-3 text-xl text-gray-600">{home.continueLearning.title}</p>
            <Link to={`/challenges/fake-post/${home.continueLearning.challengeId}`}>
              <Button variant="outline" className="mt-6">
                Resume
              </Button>
            </Link>
          </Card>
        )}
      </div>
    </div>
  );
}
