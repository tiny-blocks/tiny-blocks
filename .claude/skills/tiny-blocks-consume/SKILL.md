---
name: tiny-blocks-consume
description:
    Discover and reuse an existing tiny-blocks library as a dependency instead of writing or keeping hand-written code. Use this skill in two moments: before implementing a capability from scratch or adding a dependency from outside the ecosystem, and when reviewing or refactoring existing code, to catch where a tiny-blocks package now covers something already written by hand. It checks the catalog of published tiny-blocks packages for a candidate, adds the match with composer, and reads the installed library's own README and public API to use it correctly. Trigger on any request to implement, add, build, review, simplify, or refactor where an existing building block (collections, value objects, money, time, http, mapping, logging, identifiers, and similar) might apply.
---

# tiny-blocks consume

Reuse the ecosystem before building anew. Inside any library, when a capability is needed, the
first move is to check whether a tiny-blocks package already provides it, adopt that package, and
use its documented API. This is the consuming counterpart of `tiny-blocks-create`.

The source of truth for how to use a package is the package itself. After adding a dependency, its
README and public PHPDoc under `vendor/tiny-blocks/<name>/` are authoritative. This skill does not
copy any package API. It only points to the catalog for discovery and to the installed package for
usage.

## When to use

Use this before writing new code for a capability that is plausibly generic: collections, value
objects, money or currency, time, country codes, http primitives, object mapping, logging,
identifiers, encoding, environment variables, and similar. Also use it before reaching for any
dependency from outside the ecosystem.

Use it also when reviewing or refactoring existing code. A package may have been published after
that code was written, so check whether hand-rolled logic can now be replaced by a tiny-blocks
package. The catalog is what surfaces newly published packages, so refresh it (see below) before
concluding that nothing applies.

Do not use it for logic that is specific to the library being built and has no general building
block. In that case, write the code following the rules.

## Consume steps

1. Name the capability in one phrase, whether it is something you are about to write or something
   the existing code already does by hand (for example, "type-safe ordered collection" or "ISO
   currency with fraction digits").
2. Check `references/catalog.md` for a tiny-blocks candidate. If nothing matches and the need is
   generic, refresh the catalog (see below) and look again, since a newer package may exist.
3. If a candidate fits, add it with `composer require tiny-blocks/<name>`. Packages from the
   ecosystem are exempt from the freshness cooldown, and `composer require` prompts once before
   adding.
4. Learn the API from the installed package, not from memory. Read
   `vendor/tiny-blocks/<name>/README.md` and the public classes, interfaces, and enums under
   `vendor/tiny-blocks/<name>/src/`. Their PHPDoc and the README examples are the contract.
5. Use the package following its documented API. Transitive dependencies are resolved by composer,
   so depend on and use only the package that solves the capability directly.
6. If no candidate fits, only then write the code from scratch, or consider a dependency from
   outside the ecosystem, subject to the freshness cooldown and the `composer require` prompt.

## Catalog

`references/catalog.md` is the committed index of published tiny-blocks packages, with a one-line
purpose for each. It exists for fast, offline discovery. It is generated from Packagist, not hand
maintained. Each entry points to a package whose full API lives in its own README and PHPDoc once
installed.

## Refresh the catalog

Run `python3 scripts/refresh-catalog.py` to rebuild `references/catalog.md` from the `tiny-blocks`
vendor on Packagist. The script uses only the Python standard library, with no curl or jq, pulls
the package list plus each description, skips abandoned packages, and rewrites the list. Refresh
when a new package shipped, or when the catalog looks stale and a needed capability is not listed.

## Validate

After adding a dependency and wiring it in, run `make review` and `make tests`. Both must be green
before the work is complete. A new dependency that breaks either gate is not done.
