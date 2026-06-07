import type { SelfReportedLevel } from '@detectivelens/shared';

interface SelectionCardProps {
  level: SelfReportedLevel;
  label: string;
  icon: string;
  selected: boolean;
  onSelect: (level: SelfReportedLevel) => void;
}

export function SelectionCard({ level, label, icon, selected, onSelect }: SelectionCardProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(level)}
      className={`flex min-h-[var(--touch-min)] w-full items-center gap-5 rounded-xl border-2 px-6 py-4 text-left transition ${
        selected
          ? 'border-[var(--color-primary)] bg-[var(--color-lavender)]'
          : 'border-gray-200 bg-white hover:border-gray-300'
      }`}
    >
      <span className="text-4xl">{icon}</span>
      <span className="text-xl font-bold text-gray-800">{label}</span>
    </button>
  );
}
