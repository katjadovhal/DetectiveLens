import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

const MENU_ITEMS = [
  { label: 'Profile', to: '/profile' },
  { label: 'Statistics', to: '/profile/statistics' },
  { label: 'Settings', to: '/profile/settings' },
  { label: 'Help & Support', to: '/profile/help' },
];

export function ProfileMenu() {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex min-h-[var(--touch-min)] cursor-pointer items-center gap-2 rounded-full border-2 border-gray-200 px-3 py-1 transition hover:border-[var(--color-primary)] hover:bg-[var(--color-lavender)]"
        aria-label="Profile menu"
        aria-expanded={open}
      >
        <span className="flex h-11 w-11 items-center justify-center rounded-full bg-[var(--color-lavender)] text-xl">
          🕵️
        </span>
        <span className="text-base text-gray-500">▾</span>
      </button>

      {open && (
        <div className="absolute right-0 z-20 mt-2 w-56 rounded-xl border-2 border-gray-200 bg-white py-2 shadow-lg">
          {MENU_ITEMS.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              onClick={() => setOpen(false)}
              className="block px-5 py-3 text-lg text-gray-700 transition hover:bg-[var(--color-lavender)] hover:text-[var(--color-primary)]"
            >
              {item.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
