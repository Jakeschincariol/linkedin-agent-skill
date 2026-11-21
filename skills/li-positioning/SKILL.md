---
name: li-positioning
description: >-
  Collect and maintain the user's LinkedIn positioning, target audience, point
  of view, content pillars, writing voice, and approved evidence bank. Use
  before creating a tailored content strategy or draft when this context is
  missing, stale, or incomplete.
---

# li-positioning

Maintain the context that makes the other LinkedIn skills specific to the user.
Do not turn assumptions into positioning or personal claims.

## Required before tailored strategy or drafts

Confirm both:

1. **Target audience:** who the user wants to reach, where they work, what they
   are responsible for, and what problem or decision matters to them.
2. **Voice sample:** at least three examples of the user's own writing (such as
   LinkedIn posts, articles, or emails). Ask what to preserve or avoid if the
   samples do not make that clear.

The supplied professional context does not identify an audience or provide
voice samples. Ask for these before generating tailored positioning,
strategies, or drafts. Do not guess from job titles, geography, or industry.

## Build the positioning

Ask for the user's desired reputation and point of view, then shape:

- A one-sentence positioning statement.
- Three to five content pillars, each with a distinct reader need and the
  user's defensible perspective.
- Topics or claims to avoid, confidentiality boundaries, and preferred
  terminology.
- A voice guide based on the user's actual samples: cadence, sentence length,
  formality, vocabulary, use of first person, and patterns to avoid.

Offer a proposed version for review. Save or revise it only after the user
approves the wording. Do not treat agreement with one section as approval of
the entire file.

## Approved evidence bank

Keep evidence separate from positioning and voice:

- Add a personal claim, metric, client example, or outcome to the approved
  evidence bank only after the user explicitly confirms it may be used.
- For each item, record its source/context, timeframe, scope, the user's role,
  and any attribution or confidentiality limits. Preserve caveats.
- Claims from a supplied profile or resume, including metrics, are candidates
  only. Ask the user to confirm the figure, its definition and context, their
  attribution, and permission to use it before putting it in the approved
  bank.
- Keep unconfirmed items in a clearly marked `UNCONFIRMED - DO NOT USE` section
  only if the user wants them tracked. Never use them in copy.
- Never infer metrics, clients, results, or personal stories. Do not copy
  private contact details into these files.

## Files and compatibility

Maintain these local files, not repository files:

- `~/.claude/linkedin/positioning.md` — approved audience, positioning, POV,
  pillars, boundaries, and evidence bank.
- `~/.claude/linkedin/voice.md` — concise voice guide for `/li-post` and other
  skills that already read this file.

Read both before updating them. Preserve existing user-authored material,
show proposed edits when meaning could change, and ask before overwriting or
removing approved evidence. If the user has not approved a claim, keep it out
of copy.

## Output

Summarize what was added, what remains unconfirmed, and the next missing input.
Do not write a LinkedIn post, schedule content, or publish anything here. Use
`/li-plan` for a calendar and `/li-post` for post drafting and humanization.
