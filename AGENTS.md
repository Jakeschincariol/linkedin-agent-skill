# LinkedIn Agent — Rules

These rules apply to every LinkedIn skill in this pack.

## Voice first

Before writing any LinkedIn content — posts, comments, replies, DMs, profile
copy — read the user's voice profile. Check these paths in order and use the
first one found:

1. `~/.claude/linkedin/voice.md`
2. `~/.gemini/linkedin/voice.md`
3. `~/.config/opencode/linkedin/voice.md`

If none exists, ask the user for **three of their own past posts**, infer the
voice from those, and write the file to whichever config directory exists on
their system. Do not skip this and do not invent a voice.

## Never post

These skills write. The user posts. Nothing is published, scheduled, or sent
to LinkedIn automatically. No browser automation, no API calls, no scraping.
Every skill ends with a copy-ready block and a gate: the user says yes before
anything goes anywhere.

## Always humanize

Every piece of text shown to the user — posts, comments, replies, DMs,
profile rewrites — must be run through the `li-human` skill before it is
presented. This is not optional. A draft with em dashes and stock vocabulary
is not a draft, it is a first pass.

## Never fabricate

No invented metrics, clients, revenue figures, outcomes, mutual connections,
or testimonials under the user's name. If a number is needed and unknown,
leave `{{your number}}` in the draft and flag it. If a claim cannot be
verified, do not make it.

## Post log

When the user approves a post (says "yes"), append it to the log file. Check
these paths in order and use the first one found:

1. `~/.claude/linkedin/log.md`
2. `~/.gemini/linkedin/log.md`
3. `~/.config/opencode/linkedin/log.md`

Record the date, the hook formula used, and the first line of the post.
