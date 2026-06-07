import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { SelfReportedLevel } from '@detectivelens/shared';
import { api } from '../../services/api-client';
import { Button } from '../../components/ui/Button';
import { SelectionCard } from '../../components/ui/SelectionCard';

const LEVELS: Array<{ level: SelfReportedLevel; label: string; icon: string }> = [
  { level: 'beginner', label: 'Beginner', icon: '⭐' },
  { level: 'somewhat', label: 'Somewhat', icon: '😊' },
  { level: 'pro', label: 'Pro', icon: '🚀' },
];

export function WelcomePage() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<SelfReportedLevel>('beginner');
  const [loading, setLoading] = useState(false);
  const [welcome, setWelcome] = useState({ title: 'Hey Detective!', subtitle: '' });

  useEffect(() => {
    api.getWelcome().then(setWelcome).catch(() => {});
  }, []);

  async function handleStart() {
    setLoading(true);
    try {
      await api.completeOnboarding(selected);
      navigate('/');
    } catch {
      navigate('/');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="-mx-6 -mt-10 flex min-h-[calc(100vh-5.5rem)] flex-col items-center justify-center bg-[var(--color-lavender)] px-6 py-12 text-center sm:-mx-10 lg:-mx-16">
      <div className="w-full max-w-2xl">
        <h1 className="text-5xl font-extrabold text-gray-900 sm:text-6xl">{welcome.title}</h1>
        <p className="mx-auto mt-6 max-w-xl text-2xl text-gray-700">{welcome.subtitle}</p>

        <div className="my-12 text-9xl" role="img" aria-label="Detective character">
          🕵️‍♂️
        </div>

        <div className="mx-auto w-full max-w-lg rounded-[var(--radius-lg)] bg-white p-8 shadow-sm">
          <div className="space-y-4">
            {LEVELS.map((item) => (
              <SelectionCard
                key={item.level}
                level={item.level}
                label={item.label}
                icon={item.icon}
                selected={selected === item.level}
                onSelect={setSelected}
              />
            ))}
          </div>
          <Button className="mt-8 w-full" onClick={handleStart} disabled={loading}>
            {loading ? 'Loading...' : "Let's Go!"}
          </Button>
        </div>
      </div>
    </div>
  );
}
