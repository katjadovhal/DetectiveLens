interface ProgressBarProps {
  current: number;
  max: number;
  showLabel?: boolean;
}

export function ProgressBar({ current, max, showLabel }: ProgressBarProps) {
  const pct = Math.min(100, Math.round((current / max) * 100));

  return (
    <div className="w-full">
      {showLabel && (
        <div className="mb-3 flex justify-between text-lg font-bold text-gray-700">
          <span>Progress</span>
          <span>
            {current}/{max} Points
          </span>
        </div>
      )}
      <div className="h-5 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-[var(--color-primary)] transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
