import { useState } from 'react';
import { Button } from '../ui/Button';

export function InvestigationPanel({ hints, hintsUsed, onHintViewed }) {
  const [expanded, setExpanded] = useState(false);
  const [activeHintIndex, setActiveHintIndex] = useState(0);

  const activeHint = hints[activeHintIndex];

  return (
    <div className="mt-10 text-center">
      {!expanded ? (
        <Button variant="outline" onClick={() => setExpanded(true)}>
          Need an investigation clue?
        </Button>
      ) : (
        <div className="mx-auto max-w-2xl rounded-2xl border-2 border-gray-200 bg-gray-50 p-8 text-left">
          <p className="mb-6 text-center text-2xl font-bold text-gray-700">
            How would you like to examine this post?
          </p>
          <div className="mb-6 space-y-3">
            {hints.map((hint, i) => (
              <button
                key={hint.id}
                type="button"
                onClick={() => {
                  setActiveHintIndex(i);
                  if (i >= hintsUsed) onHintViewed();
                }}
                className={`min-h-[var(--touch-min)] w-full rounded-xl border-2 px-5 py-4 text-left text-lg ${
                  i === activeHintIndex
                    ? 'border-[var(--color-primary)] bg-white font-bold'
                    : 'border-gray-200 bg-white/60'
                }`}
              >
                {i + 1}. {hint.question}
              </button>
            ))}
          </div>
          {activeHint && (
            <div className="text-lg leading-relaxed text-gray-700">
              <p className="mb-3">{activeHint.content.body}</p>
              <p className="mb-2 text-xl font-bold">Ask yourself:</p>
              <ul className="list-inside list-disc space-y-2 text-lg">
                {activeHint.content.bulletQuestions.map((q) => (
                  <li key={q}>{q}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
