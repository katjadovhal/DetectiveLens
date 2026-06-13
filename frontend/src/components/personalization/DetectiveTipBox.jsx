export function DetectiveTipBox({ tip }) {
  return (
    <div className="mt-10 flex items-start gap-5 rounded-2xl border-2 border-[var(--color-primary)]/20 bg-[var(--color-lavender)] p-6">
      <span className="text-6xl" role="img" aria-label="Detective mascot">
        🐕
      </span>
      <div>
        <p className="mb-4 text-xl font-bold leading-relaxed text-gray-800">
          Detective Tip: {tip.message}
        </p>
        <p className="mb-3 text-lg font-bold text-gray-700">Next time, remember to:</p>
        <ul className="space-y-2 text-lg text-gray-700">
          {tip.checklist.map((item) => (
            <li key={item} className="flex items-start gap-3">
              <span className="text-2xl text-[var(--color-success)]">✓</span>
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
