export function ChallengeFeedback({
  isCorrect,
  selectedAnswer,
  correctAnswer,
  explanation,
  showExplanation,
  onToggleExplanation,
}) {
  return (
    <div className="py-12 text-center">
      {isCorrect ? (
        <>
          <p className="text-4xl font-extrabold text-gray-900 sm:text-5xl">
            You picked {selectedAnswer}! That&apos;s the fake post.
          </p>
          <p className="mt-6 text-6xl">🎉 ⭐ 🎊</p>
        </>
      ) : (
        <>
          <p className="text-4xl font-extrabold text-gray-900 sm:text-5xl">Not quite!</p>
          <p className="mt-4 text-2xl text-gray-700">
            You selected {selectedAnswer} as the fake post!
          </p>
          <p className="text-2xl text-gray-700">The correct answer was {correctAnswer}.</p>
        </>
      )}

      {!isCorrect && (
        <div className="mt-8">
          <button
            type="button"
            onClick={onToggleExplanation}
            className="min-h-[var(--touch-min)] rounded-full border-2 border-[var(--color-primary)] bg-white px-10 py-3 text-xl font-bold text-[var(--color-primary)] transition hover:bg-[var(--color-lavender)]"
          >
            Why?
          </button>
          {showExplanation && (
            <ul className="mx-auto mt-8 max-w-2xl list-inside list-disc space-y-3 text-left text-xl text-gray-700">
              {explanation.map((bullet) => (
                <li key={bullet}>{bullet}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
