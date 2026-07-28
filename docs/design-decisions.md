# Design decisions — DetectiveLens User Profile & Avatars

This document records design choices for the User Profile and Avatar Selection MVP.
It separates **evidence-based decisions** from **project assumptions**.
Where a citation from course slides is not verified in the repository, a **Reference needed** TODO is listed instead of inventing a source.

## Evidence-based decisions

### Personalization supports motivation and engagement
- **Decision:** Let children choose a detective avatar and edit their display name on a dedicated profile page.
- **Rationale:** Personalization and gamification features are widely associated with higher motivation and learning engagement in digital learning contexts, including misinformation-related games cited in project materials.
- **Status:** Supported by project literature framing (see Motivation slide).
- **TODO — Reference needed:** Verify and cite Muntean (2011); Brewer et al. (2013); Ferdiansyah (2025); Barzilai & Stadtler (2025) with full bibliographic entries before formal submission.

### Progress visibility supports persistence
- **Decision:** Show level, XP progress bar, total XP, and completed-challenge count on the profile.
- **Rationale:** Visible progress feedback helps learners understand advancement and supports continued engagement in gamified systems.
- **Status:** Aligns with project architecture (Rewards / XP & level logic) and common gamification practice.
- **TODO — Reference needed:** Add a verified source for progress visibility / persistence claims used in the avatar mockup slide.

### Age-appropriate presentation for ages ~8–12
- **Decision:** Use a small fixed set of emoji detective avatars, large touch targets, simple language, and rounded card UI consistent with the existing Kids-mode design system.
- **Rationale:** MVP targets children approximately 8–12; complex avatar generators or social features would add cognitive and privacy load without benefiting core literacy goals.
- **Status:** Project assumption grounded in the stated target group; not a literature claim by itself.

### Psychological inoculation framing (product goal, not profile UI alone)
- **Decision:** Profile identity supports the broader app goal of practicing recognition of misinformation / AI-generated visuals through repeated challenges.
- **Rationale:** Project motivation cites inoculation approaches for building resilience against misinformation.
- **TODO — Reference needed:** Verify Roozenbeek (2022) citation details before formal writing.

## Project assumptions (not claimed as empirical findings)

1. **No authentication for MVP:** Multi-user selection via `userId` query + `localStorage.lastUserId` is enough for a classroom/demo desktop web app.
2. **Emoji avatars only:** Sufficient for MVP identity; `imageUrl` is reserved for future PNG assets without changing the stored `avatarId` model.
3. **Badges (MVP, evidence-based):** Profile shows a full catalogue of locked and unlocked badges. Unlocking is deterministic from completed `challenge_attempts` only. Persisted unlock rows store `{userId, badgeId, earnedAt}` only.
4. **XP is the only progress currency:** UI labels use “XP”; no separate points field is introduced.
5. **Legacy avatar aliasing:** `detective-default` maps to `avatar-detective-1` on read/write normalization without bulk-migrating `store.json`.
6. **Accessible selection states:** Selection indicators use border + checkmark + text, not color alone.

### Badge threshold assumptions (require evaluation)
| Badge | Threshold |
|-------|-----------|
| `first_case` | ≥1 completed challenge |
| `case_solver` | ≥10 completed challenges |
| `clue_strategist` | ≥3 correct completed with `hintsUsed > 0` |
| `pattern_explorer` | ≥4 distinct `skillCategoryIds` across completed challenges |
| `detail_detective` | ≥5 completed associated with one pattern; ≥4 of last 5 relevant correct |

## Technical decisions

| Topic | Choice |
|-------|--------|
| API | Keep `GET`/`PATCH /api/v1/profiles/{user_id}` |
| Model | Existing camelCase `profiles` documents in `store.json` |
| Active user | Query `userId`, then `localStorage.lastUserId`; clear invalid IDs |
| Back navigation | `/challenge-staging?userId=…` |
| Avatar storage | Store `avatarId` string only |
| Shared UI | One avatar grid CSS for onboarding + profile |
| XP display | `profile.totalXp` for header/stat; bar uses `currentLevelXp` / `levelXpRequired` via `frontend/js/xp.js` |
| UI redesign | Light purple page background, white cards, purple primary, two-column profile, card-grid profile selection |

## UI hierarchy (2026 redesign)

- Welcome is a centered hero card; “Continue as” only appears when `lastUserId` loads a valid profile.
- Profile selection uses a responsive card grid with avatar, level, and XP (no Points labels).
- Profile creation is a single card with inline validation and a disabled submit until valid.
- Profile editing uses a two-column desktop layout that stacks on smaller screens.
- Selected states always include border + checkmark + accessible text, not color alone.
- `prefers-reduced-motion` disables non-essential transitions.

## Out of scope (explicitly deferred)

- Streak-based and leaderboard-based badges
- Avatar uploads / AI generators / PNG library
- Authentication and databases
- Public leaderboards and social features
- Reviving unused `home.js`
- New parallel `/profile` or `/avatars` endpoints
- Browser push notifications and mandatory badge sounds
