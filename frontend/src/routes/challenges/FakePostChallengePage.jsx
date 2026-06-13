import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../../services/api-client';
import { SocialPostCard } from '../../components/challenges/SocialPostCard';
import { InvestigationPanel } from '../../components/challenges/InvestigationPanel';
import { ChallengeFeedback } from '../../components/challenges/ChallengeFeedback';
import { DetectiveTipBox } from '../../components/personalization/DetectiveTipBox';
import { Button } from '../../components/ui/Button';

export function FakePostChallengePage() {
  const { id = 'burger-king-001' } = useParams();
  const navigate = useNavigate();

  const [challenge, setChallenge] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [selected, setSelected] = useState(null);
  const [hintsUsed, setHintsUsed] = useState(0);
  const [phase, setPhase] = useState('playing');
  const [result, setResult] = useState(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function load() {
      const [{ challenge: c }, start] = await Promise.all([
        api.getChallenge(id),
        api.startChallenge(id),
      ]);
      setChallenge(c);
      setSessionId(start.sessionId);
    }
    load().catch(console.error);
  }, [id]);

  async function handleSubmit(postId) {
    if (!sessionId || submitting) return;
    setSelected(postId);
    setSubmitting(true);
    try {
      const res = await api.submitFakePost(sessionId, {
        selectedPostId: postId,
        hintsUsed,
      });
      setResult(res);
      setPhase('feedback');
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  }

  if (!challenge) {
    return <div className="py-20 text-center text-gray-500">Loading challenge...</div>;
  }

  const content = challenge.content;

  if (phase === 'feedback' && result) {
    return (
      <div className="mx-auto w-full max-w-6xl">
        <ChallengeFeedback
          isCorrect={result.isCorrect}
          selectedAnswer={result.selectedAnswer}
          correctAnswer={result.correctAnswer}
          explanation={result.explanation}
          showExplanation={showExplanation}
          onToggleExplanation={() => setShowExplanation((v) => !v)}
        />
        {result.detectiveTip && <DetectiveTipBox tip={result.detectiveTip} />}
        <div className="mt-8 flex justify-end">
          <Button onClick={() => navigate('/')}>
            Next {result.xpEarned > 0 ? `(+${result.xpEarned} XP)` : ''}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-6xl">
      <div className="mb-10 text-center">
        <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl">{challenge.title}</h1>
        <p className="mt-3 text-2xl text-gray-600">{challenge.instruction}</p>
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        {content.posts.map((post) => (
          <SocialPostCard
            key={post.id}
            post={post}
            selected={selected === post.id}
            onSelect={() => handleSubmit(post.id)}
            disabled={submitting}
          />
        ))}
      </div>

      <InvestigationPanel
        hints={challenge.hints ?? []}
        hintsUsed={hintsUsed}
        onHintViewed={() => setHintsUsed((n) => Math.min(n + 1, (challenge.hints?.length ?? 0)))}
      />

      <div className="mt-10 flex items-end justify-between">
        <div className="flex items-center gap-4">
          <span className="text-6xl">🐕</span>
          <div className="rounded-2xl border-2 border-gray-200 bg-white px-6 py-4 text-xl font-medium text-gray-700 shadow-sm">
            Look closely! Not everything is what it seems!
          </div>
        </div>
      </div>
    </div>
  );
}
