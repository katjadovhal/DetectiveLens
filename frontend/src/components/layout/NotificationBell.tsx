import { useEffect, useRef, useState } from 'react';

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
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
        className="flex min-h-[var(--touch-min)] min-w-[var(--touch-min)] items-center justify-center rounded-full text-3xl transition hover:bg-gray-100"
        aria-label="Notifications"
        aria-expanded={open}
      >
        🔔
      </button>

      {open && (
        <div className="absolute right-0 z-20 mt-2 w-80 rounded-xl border-2 border-gray-200 bg-white py-3 shadow-lg">
          <p className="px-5 py-2 text-lg font-bold text-gray-800">Notifications</p>
          <p className="px-5 py-3 text-lg text-gray-600">You&apos;re all caught up! No new alerts.</p>
        </div>
      )}
    </div>
  );
}
