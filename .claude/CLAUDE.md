# tiny-blocks PHP library

A library in the [tiny-blocks](https://github.com/tiny-blocks) ecosystem: small, focused,
framework-agnostic PHP building blocks published to Packagist. Target runtime is **PHP 8.5**.

This file is the index. The detailed conventions live in `.claude/rules/` (loaded automatically
when you touch matching files) and in three skills under `.claude/skills/`. Keep this file short:
when a convention needs explaining, it belongs in a rule or a skill, not here.

## Validate

Every PHP and Composer command runs inside Docker via the `Makefile` (image
`gustavofreze/php:8.5-alpine`). Never run PHP on the host directly.

- `make review`: phpcs (PSR-12) + phpstan (`level: max`). Run before claiming code is clean.
- `make tests`: phpunit + infection. Mutation thresholds are `minMsi: 100` / `minCoveredMsi: 100`.
- `make test-file FILE=<ClassNameTest>`: one filtered test file, no coverage.
- `make help`: discover all targets if any of the above is missing or has changed.

Treat `make review` and `make tests` as the definition of done. Both gate every pull request in
CI. Passing them locally is the bar before any "complete" / "fixed" / "passing" claim.

## Conventions (`.claude/rules/`)

Path-scoped. Each loads only when you edit matching files.

- `php-library-architecture.md`: folder layout, public API boundary, `Internal/` semantics (`src/`).
- `php-library-code-style.md`: semantic code rules, naming, PHPDoc, `self`/`static` (`src/`, `tests/`).
- `php-library-modeling.md`: value objects, exceptions, enums, complexity (`src/`).
- `php-library-testing.md`: BDD Given/When/Then, PHPUnit, fixtures, coverage discipline (`tests/`).
- `php-library-tooling.md`: invariants for `composer.json`, `phpcs.xml`, `phpunit.xml`, etc.
- `php-library-documentation.md`: README and `docs/` conventions.
- `php-library-github-workflows.md`: GitHub Actions conventions.

## Skills (`.claude/skills/`)

- `tiny-blocks-create`: scaffold a new library or restore a canonical config/repo file. Holds
  the drop-in bodies of every config file, the CI workflow, and the issue/PR/security templates.
- `tiny-blocks-consume`: discover and reuse a published tiny-blocks package as a dependency
  instead of writing the capability by hand. Checks the catalog, adds the match with Composer,
  and uses the installed package's own README and public API. The consuming counterpart of
  `tiny-blocks-create`.
- `commit-message`: generate a Conventional Commits message in the ecosystem's format. Invoke
  when writing a commit. Commit messages are never generated automatically.

## Global defaults

- All identifiers, comments, documentation, and commit messages use American English.
- In prose and headings, do not use semicolons or em-dashes. This applies to PHPDoc descriptions
  and to every Markdown file (README, docs). Use a period or a comma in place of a semicolon, and
  a colon, a comma, or parentheses in place of an em-dash. Hyphens in compound words and
  identifiers (`tiny-blocks`, `name-length`) are not affected, and semicolons that terminate PHP
  statements in code are not affected.
- Prefer dependencies from the tiny-blocks ecosystem before reaching outside it.
- Do not install or update any dependency to a version published less than 7 days ago. Freshly
  released versions can be yanked or compromised. Let them age past the cooldown first. Packages
  from the tiny-blocks ecosystem (`tiny-blocks/*`) are exempt, they are first-party. When a
  dependency bump is needed but the target version is too recent, report it and wait rather than
  pinning the new version.
- Do not run any history-altering Git operation (branch, commit, push, merge, rebase, tag) unless
  explicitly asked.
