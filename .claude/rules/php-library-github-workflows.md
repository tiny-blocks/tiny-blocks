---
description: Structure, ordering, and pinning conventions for GitHub Actions workflows in PHP libraries.
paths:
    - ".github/workflows/**/*.yml"
    - ".github/workflows/**/*.yaml"
---

# Workflows

Conventions for GitHub Actions workflows in PHP libraries. CD does not apply: libraries publish to
Packagist via tags and never deploy.

The **canonical `ci.yml` body** is not duplicated here. It lives as a drop-in asset in the
`tiny-blocks-create` skill (`assets/github/workflows/ci.yml`), the single source of truth. This
rule defines the conventions that asset satisfies and that any edit to a workflow must preserve.

`ci.yml` is mandatory. Additional workflow files (security scanning, automated triage, scheduled
tasks, dependency updates) may exist and follow the general rules below. Their trigger, job
structure, and steps are chosen by their purpose. The Composer scripts invoked by `ci.yml`
(`composer review`, `composer tests`) are defined in `php-library-tooling.md`.

## Pre-output checklist

Verify every item before producing or editing any workflow YAML. If any item fails, revise before
outputting.

### Rules for every workflow

Apply to `ci.yml` and to every additional workflow in `.github/workflows/`.

1. Keys at the workflow root follow the canonical order `name`, `on`, `concurrency`,
   `permissions`, `jobs`. Absent keys are omitted. The relative order of the rest is preserved.
2. Properties inside a job follow the canonical order `name`, `needs`, `runs-on`,
   `timeout-minutes`, `outputs`, `env`, `steps`. Same omission rule.
3. Inside any block (`env`, `outputs`, `with`, `permissions`), entries are ordered by key length
   ascending.
4. The workflow `name`, every job `name`, and every step `name` are mandatory and use sentence
   case (`Resolve PHP version`, not `RESOLVE_PHP_VERSION`). Step names start with a verb. Job keys
   describe the job's purpose. Generic keys (`run`, `job`, `do`) are discouraged in favor of
   descriptive identifiers (`auto-assign`, `analyze`, `notify`).
5. `concurrency` is set at the workflow root with `cancel-in-progress: true` and a `group`
   expression scoped by the workflow's trigger, prefixed by the workflow's short purpose name
   (`ci`, `auto-assign`):
    - `pull_request`: `<purpose>-${{ github.event.pull_request.number }}`.
    - `issues`, or `issues` combined with `pull_request`:
      `<purpose>-${{ github.event.issue.number || github.event.pull_request.number }}`.
    - `push`, `schedule`, or both: `<purpose>-${{ github.ref }}`.
6. `permissions` is declared at the workflow root with the minimum scope every job needs.
   Job-level `permissions` are allowed only when a specific job needs a narrower scope than the
   root, never broader.
7. Every job sets `timeout-minutes`. Defaults: 5 for trivial steps (single API call, lightweight
   script), 15 for jobs with PHP setup or test runs, 30 for analysis-heavy jobs (security
   scanning). Adjust based on observed runtime when prior runs exist.
8. Every action is pinned to a fixed, immutable ref: a version tag at any granularity (major, minor, or patch) or a
   commit SHA. Moving refs (branch names such as @main/@master, or @v with no version) are prohibited. Do not normalize
   an explicit minor or patch pin down to its major, preserve the granularity the maintainer chose.
9. Inline shell logic longer than 3 lines is extracted to a script in `scripts/ci/`.
10. All text (workflow name, job names, step names, comments) uses American English with correct
    spelling and punctuation. Sentences and descriptions end with a period.

### Rules specific to ci.yml

Apply only to `.github/workflows/ci.yml`. Additional workflows are not bound by them.

1. File path is `.github/workflows/ci.yml`. The workflow `name` field is exactly `CI`. Per rule 5
   for every workflow, with purpose `ci` and a `pull_request` trigger, `concurrency.group` is
   `ci-${{ github.event.pull_request.number }}`.
2. Trigger is `pull_request` only. No `push`, no branch filter, no `workflow_dispatch`.
3. Jobs run in the fixed sequence `resolve-tooling-image`, `build`, `auto-review`, `tests`. Each
   downstream job lists its upstream jobs in `needs`.
4. Neither the PHP version nor the image is hardcoded in the workflow. The `resolve-tooling-image`
   job runs `make show-image` and exposes the result as the job output `php-image`, so the
   `Makefile` is the one place either is declared and CI cannot pin an image a developer never
   runs. No `setup-php` action appears: every PHP command runs in that image.
5. The `auto-review` job runs `make review`. The `tests` job runs `make tests`. No other command is
   invoked in either job, and both reach PHP through the `Makefile` rather than through a runtime
   installed on the runner.
6. The `build` job uploads `vendor/` and `composer.lock` as a single artifact named
   `vendor-artifact`. The `auto-review` and `tests` jobs download that artifact instead of
   running `composer install` again.
7. The `tests` job is the only job that may extend with extra setup the library needs (service
   containers, fixture preparation, environment variables used during testing). The other three
   jobs are identical across every library in the ecosystem.
8. `timeout-minutes` is 5 for `resolve-tooling-image` and 15 for `build`, `auto-review`, and
   `tests`. `permissions` is `contents: read`.

## ci.yml job sequence

`ci.yml` gates every pull request with four jobs in this exact order. The first three are
identical across every library. Only `tests` may extend.

- **Resolve tooling image.** Runs `make show-image` and exposes the result as the output
  `php-image`. One step, and the `Makefile` stays the only declaration of what PHP runs on.
- **Build.** Validates `composer.json` and installs with
  `--no-progress --optimize-autoloader --prefer-dist --no-interaction`, both inside the resolved
  image mounted at `/var/www/html`, then uploads `vendor/` and `composer.lock` as
  `vendor-artifact`.
- **Auto review.** Needs `resolve-tooling-image` and `build`. Downloads `vendor-artifact` and runs
  `make review` (phpcs + phpstan).
- **Tests.** Needs `resolve-tooling-image` and `auto-review`. Downloads `vendor-artifact` and runs
  `make tests` (phpunit + infection). Library-specific test setup lives in this job only.

To extend the `tests` job (external services, env vars, fixtures), the additions go inside the
`tests` job exclusively. The skill asset includes an extended example with a MySQL service
container.
