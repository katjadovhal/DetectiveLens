# Challenge Data

JSON challenge definitions consumed by `backend/prisma/seed.ts`.

## Authoring a fake-post challenge

See `fake-post/burger-king-001.json` for the reference format.

Required fields: `slug`, `type`, `difficulty`, `title`, `instruction`, `skillCategoryIds`, `xpReward`, `content`, `hints`.

## Types

- `fake-post/` — Which post is fake?
- `is-it-real/` — Real vs AI binary decision
- `find-clues/` — Hotspot selection on AI images
- `assessment/` — Onboarding diagnostic questions
- `library/` — Learning Library markdown content
