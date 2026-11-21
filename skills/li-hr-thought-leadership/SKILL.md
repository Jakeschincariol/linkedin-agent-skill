---
name: li-hr-thought-leadership
description: >-
  Turn the user's real HR leadership experience into credible LinkedIn
  thought-leadership angles, idea briefs, and drafts. Use for posts about HR
  strategy, business partnering, talent, organizational development,
  workforce planning, or AI-enabled HR.
---

# li-hr-thought-leadership

Find the sharp, useful lesson in what the user actually did, saw, changed, or
questioned. The goal is professional visibility and thought leadership, not a
generic HR explainer or a sales pitch.

## Before ideation or drafting

Read `~/.claude/linkedin/positioning.md` and `~/.claude/linkedin/voice.md` if
they exist. If either the target audience or voice sample is missing or
unconfirmed, ask the user for them before generating tailored ideas, strategy,
or drafts; they can run `/li-positioning` to collect and save that context.
Do not assume an audience or invent a voice.

The user-supplied professional context is a starting lens, not a set of
approved public claims: HR strategy leadership and founding a Saudi-based HR
advisory practice, with experience across HR business partnering, talent,
organizational development, workforce planning, and AI-enabled HR. Confirm
that a detail is current, accurate, attributable to the user, and appropriate
to share before using it as a personal claim.

## Find the real material

Ask for a concrete situation when the prompt is only a broad topic. Useful
prompts include: What happened? What decision was difficult? What did the user
try? What changed, surprised them, or did not work? What could they share
without exposing a person, client, or employer?

Build angles from the user's answer, not from assumptions about Saudi Arabia,
HR practices, or AI. Prefer a specific tension, trade-off, changed belief, or
lesson over generic advice. Do not make up dialogue, scenes, client details,
numbers, outcomes, or lessons.

## Evidence and confidentiality

Use claims from the approved evidence bank in
`~/.claude/linkedin/positioning.md` only within their recorded context and
limits. A metric appearing in the supplied profile PDF is a candidate, not
permission to publish it. Ask the user to confirm its definition, timeframe,
scope, attribution, and permission before using it. If proof is missing,
remove the claim or mark a clear question for the user; never fill the gap
with a plausible number.

Generalize or omit confidential details. Do not include names, private contact
details, identifiable employee/client information, or internal data unless
the user confirms it is appropriate to disclose.

## Output

For ideation, return a short list of distinct idea briefs. Each should include
the audience need, the user's true experience or evidence behind it, the
point of view, and any fact that still needs confirmation. Recommend one
angle and explain why it is both useful and supportable.

When asked for a draft, write from the approved positioning and the specific
experience the user supplied. Flag unresolved facts inline rather than
silently smoothing over them. Keep human review explicit; the user decides
what represents them and posts manually.

This skill does not replace adjacent skills: use `/li-plan` for scheduling,
`/li-post` for hook options and post humanization, and `/li-comment` for
responding to another person's post. Never automate LinkedIn actions or post
on the user's behalf.
