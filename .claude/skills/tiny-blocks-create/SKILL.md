---
name: tiny-blocks-create
description: Scaffold a new PHP library for the tiny-blocks ecosystem, or restore a single canonical config/repository file (composer.json, phpcs.xml, phpunit.xml, phpstan.neon.dist, infection.json.dist, .editorconfig, .gitattributes, .gitignore, Makefile, the CI workflow, SECURITY.md, the issue templates, the PR template, the Copilot instructions) to its standard shape. Use this skill whenever the user asks to create, bootstrap, set up, or initialize a new tiny-blocks library, to add the standard config/tooling files to a repository, or to fix/regenerate any of those files to match the ecosystem standard, even if they only mention one file by name. This skill owns the canonical bodies of those files. Do not hand-write them from memory.
---

# tiny-blocks library scaffolding

This skill is the single source of truth for the boilerplate every tiny-blocks PHP library
shares: the config files, the CI workflow, and the repository templates. The canonical bodies
live in `assets/` as drop-in files. Copy them and substitute the placeholders rather than
regenerating them from memory. The assets already encode the ecosystem's decisions (the `PSR12`
plus `SlevomatCodingStandard` ruleset, `level: max`, MSI 100, Docker-wrapped Makefile, the
`.dist` naming split, the export-ignore set).

The semantic conventions (how to name classes, how to structure `src/`, how to write tests) are
**not** in this skill. They live in `.claude/rules/`. This skill produces the skeleton. The rules
govern the code you then write into it.

## When to use which mode

- **Full scaffold**: the user is starting a new library. Create the directory skeleton and copy
  every asset, substituting placeholders.
- **Single-file restore**: the user wants one file brought back to standard (for example, "fix
  my Makefile" or "regenerate the CI workflow"). Copy only that asset. Do not touch the rest.

## Asset map

Copy each asset to the path on the right, relative to the repository root.

| Asset (`assets/…`)                         | Destination                                 | Placeholders |
|--------------------------------------------|---------------------------------------------|--------------|
| `config/composer.json`                     | `composer.json`                             | yes          |
| `config/phpcs.xml`                         | `phpcs.xml`                                 | no           |
| `config/phpstan.neon.dist`                 | `phpstan.neon.dist`                         | no           |
| `config/phpunit.xml`                       | `phpunit.xml`                               | no           |
| `config/infection.json.dist`               | `infection.json.dist`                       | no           |
| `config/.editorconfig`                     | `.editorconfig`                             | no           |
| `config/.gitattributes`                    | `.gitattributes`                            | no           |
| `config/.gitignore`                        | `.gitignore`                                | no           |
| `config/Makefile`                          | `Makefile`                                  | no           |
| `github/workflows/ci.yml`                  | `.github/workflows/ci.yml`                  | no           |
| `github/ISSUE_TEMPLATE/bug_report.md`      | `.github/ISSUE_TEMPLATE/bug_report.md`      | no           |
| `github/ISSUE_TEMPLATE/feature_request.md` | `.github/ISSUE_TEMPLATE/feature_request.md` | no           |
| `github/PULL_REQUEST_TEMPLATE.md`          | `.github/PULL_REQUEST_TEMPLATE.md`          | no           |
| `github/copilot-instructions.md`           | `.github/copilot-instructions.md`           | no           |
| `docs/SECURITY.md`                         | `SECURITY.md`                               | yes          |

## Placeholders

Two assets carry placeholders. Substitute every occurrence.

| Placeholder                                             | Meaning                                      | Example                   |
|---------------------------------------------------------|----------------------------------------------|---------------------------|
| `<lib-name>`                                            | Repository name, kebab-case                  | `event-sourcing`          |
| `<LibName>`                                             | PSR-4 namespace segment, PascalCase          | `EventSourcing`           |
| `<one short sentence describing what the library does>` | `composer.json` `description` (one sentence) | n/a                       |
| `<topic-1>`, `<topic-2>`                                | `composer.json` `keywords` topic tokens      | `psr-7`, `event-sourcing` |

`<lib-name>` appears in `composer.json` (`name`, `homepage`, `support`) and in `SECURITY.md`
(advisory URL). `<LibName>` appears only in `composer.json` (`autoload` / `autoload-dev` PSR-4
prefixes). The first `keywords` entry is always `tiny-blocks`. The topic tokens follow.

## Full scaffold steps

1. Confirm `<lib-name>`, `<LibName>`, the one-sentence description, and the keyword topics with
   the user if not already known.
2. Create the directory skeleton:
   ```
   src/
   tests/
   .github/workflows/
   .github/ISSUE_TEMPLATE/
   ```
3. Copy every asset to its destination (table above), substituting placeholders.
4. Author the files this skill does **not** carry, following the rules:
   - `README.md`: follow `php-library-documentation.md` (title, license badge, TOC, the fixed
     section order, code-example rules).
   - `LICENSE`: MIT, attributed to the author in `composer.json`.
   - Initial `src/` and `tests/`: follow `php-library-architecture.md`,
     `php-library-code-style.md`, `php-library-modeling.md`, and `php-library-testing.md`.
5. Register the new library in the ecosystem dependency graph at `doc/dependency-graph.excalidraw`
   in the `tiny-blocks` meta repository. A new library is a new node even when it depends on
   nothing. See `ecosystem-dependency-graph.md` for what has to move together.
6. Validate (see below) before reporting the scaffold complete.

## The .dist naming split

The assets deliberately commit `phpcs.xml` and `phpunit.xml` as live files, but
`phpstan.neon.dist` and `infection.json.dist` with the `.dist` suffix. This is intentional and
documented in `php-library-tooling.md`: the ruleset and the test config are stable and committed
live. PHPStan and Infection are the two tools a contributor may tune locally, so a gitignored
`phpstan.neon` / `infection.json` overrides the committed `.dist` baseline. Do not add a `.dist`
twin for `phpcs.xml`/`phpunit.xml`, and do not commit a live `phpstan.neon`/`infection.json`.

## Extending the CI tests job

`ci.yml` is the minimal canonical workflow. Only the `tests` job may be extended, and only when
the library's tests need external services, environment variables, or fixture preparation. Add
them inside the `tests` job. Leave `resolve-tooling-image`, `build`, and `auto-review` untouched.
Example with a MySQL service container:

```yaml
tests:
  name: Tests
  needs: [resolve-tooling-image, auto-review]
  runs-on: ubuntu-latest
  timeout-minutes: 15
  env:
    DB_HOST: 127.0.0.1
    DB_NAME: library_test
    DB_PORT: '3306'
    DB_USER: library
    DB_PASSWORD: library
  services:
    mysql:
      image: mysql:8
      ports:
        - 3306:3306
      env:
        MYSQL_DATABASE: library_test
        MYSQL_ROOT_PASSWORD: library
      options: >-
        --health-cmd="mysqladmin ping"
        --health-interval=10s
        --health-timeout=5s
        --health-retries=5
  steps:
    - name: Checkout
      uses: actions/checkout@v7

    - name: Download vendor artifact from build
      uses: actions/download-artifact@v8
      with:
        name: vendor-artifact
        path: .

    - name: Run tests
      run: make tests
```

The extended job still reaches PHP through `make`, never through a runtime installed on the
runner. Service containers, environment variables, and fixture steps are the only additions.

## Pinned action versions

The action versions pinned in `ci.yml` (`actions/checkout@v7`, `actions/upload-artifact@v7`,
`actions/download-artifact@v8`) may be outdated. Before adopting the workflow, verify the current
major version of each action and update the pin while preserving the `@vN` prefix style, as
required by `php-library-github-workflows.md` rule 8. No `setup-php` action appears: the tooling
image resolved by `make show-image` carries the runtime.

## Validate

After scaffolding (or restoring `composer.json`/the test config), run the toolchain through the
Makefile and confirm both pass before reporting done:

- `make review`: phpcs (PSR-12) and phpstan (`level: max`) must pass clean.
- `make tests`: phpunit and infection must pass with MSI 100 / covered MSI 100.

If `make` targets are missing, `make help` lists them. Do not claim the scaffold is complete on
the strength of file creation alone. The definition of done is a clean `review` and `tests`.
