---
description: Keeping the ecosystem dependency graph in sync when a library dependency changes.
paths:
    - "composer.json"
---

# Ecosystem dependency graph

The `tiny-blocks` meta repository publishes `doc/dependency-graph.svg`, which records how the
libraries depend on each other. It is derived from the `require` and `require-dev` sections of
every library's `composer.json`, so it goes stale the moment one of them changes.

## When to update it

Update the graph in the same change that does any of the following:

- Adds a `tiny-blocks/*` package to `require` or `require-dev`.
- Removes a `tiny-blocks/*` package from `require` or `require-dev`.
- Moves a `tiny-blocks/*` package between `require` and `require-dev`, because the two are drawn
  differently and only `require` counts toward the layers.
- Creates a new library, which adds a node even when that library depends on nothing.
- Renames or archives a library.

Changes to packages outside the `tiny-blocks` namespace do not affect the graph. A version bump of
an existing `tiny-blocks/*` dependency does not affect it either, because the graph records edges
and not versions.

## What to update

The diagram is drawn in `doc/dependency-graph.excalidraw` and exported to `doc/dependency-graph.svg`, which is
what the README embeds. Both files move together, and so do the parts inside them:

1. The two groups. A library belongs to the first group when it requires no other `tiny-blocks`
   package, and to the second when it requires at least one.
2. The card for every library the change touches, both the one being edited and the one it now
   depends on, since the second gains or loses a consumer.
3. The consumer list and its count on each affected card. A consumer that appears only in
   `require-dev` is suffixed `(dev)`.
4. The card color, which follows the consumer count: four or more consumers is a hub, one or more
   is a library, dev-only consumers is test-only, and none is unused.

State the counts you computed rather than carrying the previous ones forward. Re-export the SVG
after editing the `.excalidraw` file, otherwise the README keeps showing the old picture.

## Where it lives

The document lives in the `tiny-blocks` meta repository, not in the library being edited. When a
library's `composer.json` changes and the meta repository is not part of the current checkout, say
so and report the new edges instead of silently skipping the update.
