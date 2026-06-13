export function SocialPostCard({ post, selected, onSelect, disabled }) {
  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={disabled}
      className={`relative w-full rounded-2xl border-2 p-6 text-left transition ${
        selected
          ? 'border-[var(--color-primary)] ring-4 ring-[var(--color-primary)]/20'
          : 'border-gray-200 hover:border-[var(--color-primary)]/50'
      } ${disabled ? 'cursor-default' : 'cursor-pointer'}`}
    >
      <span className="absolute -left-4 -top-4 flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-primary)] text-xl font-bold text-white">
        {post.id}
      </span>

      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-orange-100 text-2xl font-bold text-orange-600">
          BK
        </div>
        <div>
          <div className="flex items-center gap-2 text-xl font-bold text-gray-900">
            {post.author}
            {post.verified && <span className="text-2xl text-blue-500">✓</span>}
          </div>
          <div className="text-lg text-gray-500">{post.handle}</div>
        </div>
      </div>

      <p className="mb-4 text-xl leading-relaxed text-gray-800">{post.text}</p>

      {post.imageUrl && (
        <div className="mb-4 flex h-44 items-center justify-center rounded-xl bg-orange-50 text-6xl">
          🍔
        </div>
      )}

      <div className="flex flex-wrap gap-4 text-base text-gray-500">
        {post.metrics.retweets != null && <span>{post.metrics.retweets.toLocaleString()} Retweets</span>}
        {post.metrics.likes != null && <span>{post.metrics.likes.toLocaleString()} Likes</span>}
      </div>
      <div className="mt-2 text-base text-gray-400">{post.timestamp}</div>
    </button>
  );
}
