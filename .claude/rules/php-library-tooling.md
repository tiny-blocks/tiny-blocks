---
description: Invariants for the canonical config files of PHP libraries in the tiny-blocks ecosystem.
paths:
    - "composer.json"
    - "phpcs.xml"
    - "phpstan.neon"
    - "phpstan.neon.dist"
    - "phpunit.xml"
    - "infection.json"
    - "infection.json.dist"
    - ".editorconfig"
    - ".gitattributes"
    - ".gitignore"
    - "Makefile"
---

# Tooling

Invariants that every config file in a tiny-blocks library must satisfy. The **canonical file
bodies** (full `composer.json`, `Makefile`, `phpunit.xml`, etc.) are not duplicated here. They
live as drop-in assets in the `tiny-blocks-create` skill, which is the single source of truth
for scaffolding a new library or restoring a file to its canonical shape. This rule defines the
invariants those files are checked against when editing an existing library.

Folder structure lives in `php-library-architecture.md`. Code style lives in
`php-library-code-style.md`.

## Pre-output checklist

Verify every item before creating, editing, or relocating any config file. If any item fails,
revise before outputting.

1. The repository root contains all of: `composer.json`, `phpcs.xml`, `phpstan.neon.dist`,
   `phpunit.xml`, `infection.json.dist`, `.editorconfig`, `.gitattributes`, `.gitignore`,
   `Makefile`. (See "Config file naming" for which carry a `.dist` suffix and why.)
2. `composer.json` exposes exactly five scripts: `configure`, `configure-and-update`, `review`,
   `test-file`, `tests`. No other public scripts.
3. `composer.json` fixed fields use the canonical values from the skill asset (`license`, `type`,
   `minimum-stability`, `prefer-stable`, `authors`, `config`, `require.php`). The six universal
   dev dependencies (`ergebnis/composer-normalize`, `infection/infection`, `phpstan/phpstan`,
   `phpunit/phpunit`, `slevomat/coding-standard`, `squizlabs/php_codesniffer`) are present, and
   `config.allow-plugins` enables `dealerdirect/phpcodesniffer-composer-installer` so the Slevomat
   sniffs register with phpcs. `require-dev` may add libraries the tests need on top of those six.
   The asset's caret ranges are the canonical floor, and the repo `composer.json` matches the
   asset. To bump, update the asset first, then the repo.
4. `composer.json` `description` is a single short sentence. Multi-sentence prose belongs in the
   README Overview, not in Composer metadata.
5. `composer.json` includes a `keywords` array that contains `"tiny-blocks"`. Its position in
   the array is not constrained. The remaining entries are topic tokens derived from the
   library's purpose (`psr-7`, `http-client`, `event-sourcing`, etc.).
6. `phpcs.xml` references the `PSR12` ruleset plus curated Squiz, Generic, PSR2, and
   `SlevomatCodingStandard` sniffs that mechanically enforce the library's structural and
   type-hint conventions (class member order, alphabetically sorted and used-only imports, strict
   types, parameter, property, and return type hints, and complexity ceilings). The
   `SlevomatCodingStandard.Classes.ClassStructure` groups collapse all methods into one group, so
   the `php-ordering-conformance` hook owns the name-length ordering within them. The three
   formatting rules the ruleset does not cover live in `php-library-code-style.md` under
   "Formatting overrides".
7. `phpunit.xml` sets all five `failOn*` flags to `true` (`failOnDeprecation`, `failOnNotice`,
   `failOnPhpunitDeprecation`, `failOnRisky`, `failOnWarning`).
8. `phpunit.xml` sets `executionOrder="random"` and `beStrictAboutOutputDuringTests="true"`.
   Non-namespace root attributes are sorted alphabetically. The `xmlns:xsi` and
   `xsi:noNamespaceSchemaLocation` declarations lead the attribute list and are not part of
   the alphabetical run.
9. `infection.json.dist` sets `minMsi: 100` and `minCoveredMsi: 100`. Lowering either is
   prohibited.
10. `.editorconfig` sets `max_line_length = 120`, `indent_size = 4`, `indent_style = space`,
    `end_of_line = lf` as the global default under `[*]`. YAML uses `indent_size = 2` and
    Makefile uses `indent_style = tab` as per-extension overrides.
11. `.gitattributes` sets `* text=auto eol=lf` and lists every committed dev-only file under
    `export-ignore`. The Packagist tarball contains only `src/`, `composer.json`, `README.md`,
    `LICENSE`, and `SECURITY.md`. `.claude/` is listed under `export-ignore` (versioned on
    GitHub for contributor parity, excluded from the published package), and `CLAUDE.md` (where
    committed) is `export-ignore`d alongside it for the same reason. `.gitattributes` lists
    only files that are actually committed: it never names a file the repository does not
    contain (no `CONTRIBUTING.md`, which is centralized, and no phantom `.dist`/non-`.dist`
    twin of a file that is committed under only one of those names).
12. `.gitignore` ignores the dependency and artifact paths, the local config overrides
    (`/phpstan.neon`, `/infection.json`), and nothing tool caches the project does not produce.
    The `.claude/` directory itself is **not** ignored (it is versioned on GitHub). Only
    `/.claude/settings.local.json`, the per-clone settings override, is ignored.
13. `Makefile` wraps every PHP and Composer command in Docker using the canonical image
    `gustavofreze/php:8.5-alpine`. No PHP command runs on the host directly. Targets that share
    a name with a Composer script delegate to it. Additional non-Composer convenience targets
    (`help`, `clean`, `show-*`) are permitted.
14. All test artifact paths use `reports/` (plural), consistent across `composer tests`,
    `infection.json.dist`, `phpunit.xml`, and `Makefile`. `reports/` is listed under
    `export-ignore` in `.gitattributes`.

## Config file naming

The committed config files split into two naming conventions on purpose. The split is documented
here so it reads as intentional, not accidental.

- **Committed live, no `.dist`:** `phpcs.xml` and `phpunit.xml`. The ruleset (`PSR12` plus the
  curated Squiz, Generic, PSR2, and `SlevomatCodingStandard` sniffs) and the test configuration
  are stable across the whole ecosystem and identical in every library. There is no per-clone
  local-override story, so the live file is committed directly.
- **Committed as `.dist`:** `phpstan.neon.dist` and `infection.json.dist`. These are the two
  tools a contributor may legitimately want to tune locally (a temporary `ignoreErrors` entry, a
  narrower mutator set while iterating). The `.dist` baseline is committed. A contributor drops a
  gitignored `phpstan.neon` or `infection.json` to override it, and the tool auto-resolves the
  override over the `.dist` fallback. Those override names appear in `.gitignore`.

Do not introduce a `.dist` twin for `phpcs.xml`/`phpunit.xml`, and do not commit a live
`phpstan.neon`/`infection.json` in place of the `.dist` baseline.

## phpstan ignoreErrors

`phpstan.neon.dist` runs at `level: max` on `src` and `tests`. `ignoreErrors` is permitted to
suppress legitimate false positives produced by `level: max` (third-party signatures carrying
`mixed`, PHP-FIG interfaces returning untyped arrays, trait unused-method warnings on shared
behavior, and the typed-array cases routed here by `php-library-code-style.md` instead of adding
PHPDoc). Each entry follows these rules:

- A short comment above the entry justifies its existence.
- Prefer scoping via `identifier:` plus `path:` over raw `#...#` message patterns.
- `reportUnmatchedIgnoredErrors: true` is mandatory. Obsolete entries fail the build, forcing
  cleanup.

```neon
ignoreErrors:
    # Trait method intentionally unused by the consuming aggregate. Reflection wires it.
    - identifier: trait.unused
      path: src/Internal/EventualAggregateRootBehavior.php
```

## Infection mutator config

`infection.json.dist` is configured with `"mutators": {"@default": true}`. That is the only
permitted form. No `ignore` lists, no `ignoreSourceCodeByRegex`, and no per-mutator overrides
are allowed. Every mutant the default profile produces must be killed by a test. When a mutant
escapes, the production code is refactored to make it testable rather than the configuration
relaxed. This aligns with `php-library-testing.md` rule 15 (no mutant suppression by any
mechanism) and with the MSI 100 thresholds in checklist item 9.

## Composer scripts

The five scripts and their purpose. Bodies live in the skill asset.

- `composer configure` installs with `--optimize-autoloader` then normalizes. Run after cloning
  or pulling.
- `composer configure-and-update` updates dependencies then normalizes. Run when intentionally
  bumping dependencies.
- `composer review` runs `phpcs` then `phpstan`. Used by CI (`auto-review` job) and locally.
- `composer tests` runs `phpunit` then `infection`. Used by CI (`tests` job).
- `composer test-file <FilterPattern>` runs a filtered subset without coverage. Local only.
