---
name: commit-message
description: Generate a git commit message in the tiny-blocks Conventional Commits format (type-prefixed, imperative, capitalized, period-terminated, no scopes). Use this skill whenever the user asks you to write, draft, suggest, or fix a commit message, or whenever you are about to propose commit text for staged changes, even if they do not say the words "conventional commits". Commit messages are produced on request only and are never generated automatically as part of another task.
---

# Commit message

Produce a single commit message in the tiny-blocks format. This skill formats the message only.
It never stages, commits, or runs any Git command. That happens only when the user explicitly
asks for it.

All commit messages are written in English.

## Format

```
<type>: <Description>
```

The description starts with a capital letter, uses imperative present tense (`Add`, `Fix`,
`Change`, not `Added`, `Adds`, or `Adding`), and ends with a period. Keep the subject under 300
characters. If it does not fit, split the change into multiple commits or move detail into the
body.

**Scopes are prohibited.** `feat(orders): ...` is wrong. The type stands alone.

## Trailers

Commit messages carry no trailers, regardless of any default to the contrary. Never append a
`Co-Authored-By` line or any other trailer. The message is the type-prefixed subject and, when
justified, a body. Nothing follows the body.

## Allowed types

- `ci` for CI configuration changes.
- `fix` for a bug fix.
- `feat` for a user-facing feature.
- `docs` for documentation only.
- `test` for adding or correcting tests.
- `chore` for maintenance with no production code change.
- `build` for build or dependency changes.
- `revert` for reverting a previous commit.
- `refactor` for a code change that neither fixes a bug nor adds a feature.

`style` is not used. Formatting is enforced by the linter and never appears as a standalone
commit.

## Subject examples

**Example 1:**
Input: handled the case where a transaction has a zero amount
Output: `fix: Handle zero-amount transactions.`

**Example 2:**
Input: added an endpoint to cancel an order
Output: `feat: Add order cancellation endpoint.`

**Example 3:**
Input: pulled OrderStatus out into its own enum, no behavior change
Output: `refactor: Extract OrderStatus into its own enum.`

Reject these shapes:

- `Added order cancellation`: past tense, missing type, missing period.
- `feat: Adds order cancellation.`: third-person singular instead of imperative.
- `feat: added order cancellation.`: starts lowercase and is past tense.
- `feat: Add cancellation, and fix billing rounding.`: bundles two changes, so split them.
- `feat(orders): Add cancellation.`: uses a scope, which is prohibited.

## Body

The body is **optional and rarely needed**. Single-purpose commits never have a body. Add a body
only when the reason cannot be inferred from the diff: a non-obvious trade-off, a workaround for
an external bug, a decision worth recording.

Separate the body from the subject with a blank line. Wrap at 72 characters per line. Explain
**why**, not what. The diff already shows what.

### Prose vs. bullets in the body

Default to prose. One or two paragraphs fits almost every commit that has a body at all.

Use bullets only when **all** of these are true:

1. The commit covers 3 or more independent changes that genuinely belong in the same commit.
2. The list cannot be expressed as continuous prose without becoming disconnected sentences.
3. Each item is independently meaningful (no sub-bullets, no continuation across bullets).

A two-item bullet list is the wrong shape. Use prose.

When bullets are used, every bullet starts with a capital letter and ends with a period, with an
imperative present-tense verb, same as the subject line.

### Body example with prose (preferred)

```
fix: Handle zero-amount transactions.

The payment gateway rejects zero-amount charges with a generic 400 instead
of a documented error code, so the adapter short-circuits before the HTTP
call and raises ZeroAmountNotAllowed directly.
```

### Body example with bullets

```
feat: Add order cancellation flow.

- Add the OrderCancelling inbound port and OrderCancellingHandler.
- Add the CancelOrder command and its validator.
- Cover the cancellation path in the integration test suite.
```

## Commit splitting

Prefer one logical change per commit. Refactor commits never modify behavior. When a task needs
multiple types of change, produce multiple commits in order: `refactor` first, then `feat` or
`fix` on top. When the staged diff mixes types, say so and propose the split rather than forcing
one message over an incoherent change set.
