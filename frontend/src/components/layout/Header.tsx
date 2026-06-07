import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../services/api-client';
import { NotificationBell } from './NotificationBell';
import { ProfileMenu } from './ProfileMenu';

export function Header() {
  const [xp, setXp] = useState(320);

  useEffect(() => {
    api.getHome().then((home) => setXp(home.progress.totalXp)).catch(() => {});
  }, []);

  return (
    <header className="sticky top-0 z-10 flex w-full items-center justify-between border-b-2 border-gray-200 bg-white px-6 py-5 sm:px-10 lg:px-16">
      <Link to="/" className="flex items-center gap-3 text-2xl font-extrabold text-gray-800">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-primary)] text-2xl text-white">
          🕵️
        </span>
        DetectiveLens
        <span className="text-[var(--color-diamond)]">🔍</span>
      </Link>

      <div className="flex items-center gap-3 sm:gap-5">
        <Link
          to="/progress/xp"
          className="flex min-h-[var(--touch-min)] cursor-pointer items-center gap-2 rounded-full px-3 py-2 text-xl font-bold text-[var(--color-diamond)] transition hover:bg-blue-50"
          title="View your XP and level"
        >
          <span className="text-2xl">💎</span>
          <span>{xp}</span>
        </Link>
        <NotificationBell />
        <ProfileMenu />
      </div>
    </header>
  );
}
