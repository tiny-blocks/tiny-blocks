---
description: Conventions for README and public-facing Markdown docs in PHP libraries.
paths:
    - "README.md"
    - "docs/**/*.md"
---

# Documentation

Conventions for `README.md` and the public-facing Markdown a library ships. PHPDoc rules for
`.php` files live in `php-library-code-style.md`. American English applies everywhere (see the
American English section in `php-library-code-style.md`).

The **canonical bodies** of the non-README repository files (`SECURITY.md`, the issue templates,
the pull request template) are not duplicated here. They live as drop-in assets in the
`tiny-blocks-create` skill, the single source of truth for those files. This rule governs how
the README and any `docs/` Markdown are written. "Required repository files" below lists which
files must exist and points to the skill for their content.

`CONTRIBUTING.md` is centralized at
`https://github.com/tiny-blocks/tiny-blocks/blob/main/CONTRIBUTING.md`. Each library's README and
pull request template link to that location. No local `CONTRIBUTING.md` is created per library.

## Pre-output checklist

Verify every item before producing any Markdown documentation. If any item fails, revise before
outputting.

1. README title is `# <LibName>` with spaces between words (`# Building Blocks`, not
   `# BuildingBlocks`).
2. License badge is the only badge. No build, coverage, Packagist, or version badges.
3. Header is followed by an anchor-linked table of contents.
4. Table of contents uses `*` for top-level (H2) entries, `+` indented by 4 spaces for
   second-level (H3) entries, and `-` indented by 8 spaces for third-level (H4) entries. Every
   heading from the document appears in the TOC, except FAQ entries: the FAQ is represented by a
   single `* [FAQ](#faq)` line regardless of how many questions it contains.
5. Sections appear in the canonical order: Overview, Installation, How to use, FAQ (optional),
   License, Contributing.
6. FAQ exists only when there are genuine points of confusion or unusual design decisions. Skip
   it entirely when not needed.
7. **Self-contained code examples** are blocks that include any of: a `use` statement, a
   `class`/`enum`/`interface`/`trait`/`function` declaration, or more than 3 lines of executable
   code. Self-contained blocks open with `<?php`, a blank line, `declare(strict_types=1);`, and
   every `use` statement required to compile.
8. **Inline fragment examples** are blocks with at most 3 lines of executable code, no `use`
   statements, and no type declarations. Fragments may omit the prologue.
9. Inline comments in PHP code examples (inside Markdown files) use `#` for single-line.
   Multi-line comments use consecutive `#` lines, all aligned at the same indentation level.
   `//` and `/* */` are not used in examples.
10. Tables are used for structured data such as constructor parameter lists, builder method
    catalogs, configuration options, or complexity tables. Column layout is chosen per case.
11. FAQ entries use the heading format `### NN. <Question>?` with zero-padded numbering
    (`### 01.`, `### 02.`).
12. FAQ bibliographic citations use the format
    `> Author, *Title* (Publisher, Year), Chapter X, "Section Name".`
13. License and Contributing sections each follow the canonical one-line template.
14. The repository contains the required non-README files listed in "Required repository files",
    each matching its canonical asset in the `tiny-blocks-create` skill.

## README

### Structure

The README follows a fixed section order:

1. **Overview**. One or more paragraphs explaining the problem the library solves and its design
   philosophy. Cross-references to related `tiny-blocks` libraries belong here.
2. **Installation**. Composer command in a code block, with no surrounding prose unless strictly
   necessary.
3. **How to use**. Runnable examples covering the primary use cases. Each subsection demonstrates
   one capability with a heading and a self-contained code block.
4. **FAQ** (optional). Numbered questions that address real points of confusion or unusual design
   decisions.
5. **License**. One-line link to the `LICENSE` file.
6. **Contributing**. One-line link to the centralized `CONTRIBUTING.md` in
   `tiny-blocks/tiny-blocks`.

### Header and license badge

The first line is `# <LibName>` followed by a blank line and the license badge:

```markdown
# Outbox

[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/tiny-blocks/<lib-name>/blob/main/LICENSE)
```

Replace `<lib-name>` with the library's repository name. The badge is the only badge in the
document.

### Table of contents

The table of contents is anchor-linked. Top-level (H2) entries use `*`. Second-level (H3) entries
use `+` indented by 4 spaces. Third-level (H4) entries use `-` indented by 8 spaces. Every heading
from the document appears, with one exception: the FAQ is represented by a single
`* [FAQ](#faq)` line. Its questions never appear as TOC sub-entries, regardless of how many exist.

```markdown
* [Overview](#overview)
* [Installation](#installation)
* [How to use](#how-to-use)
    + [Subtopic A](#subtopic-a)
    + [Subtopic B](#subtopic-b)
* [FAQ](#faq)
* [License](#license)
* [Contributing](#contributing)
```

Use the third level whenever the document has H4 headings. The TOC mirrors the document structure
exactly.

### Code examples

Code examples fall into two categories.

**Self-contained examples** include at least one of these: a `use` statement, a
`class`/`enum`/`interface`/`trait`/`function` declaration, or more than 3 lines of executable code.
They open with `<?php`, a blank line, and `declare(strict_types=1);`, and carry every `use`
statement required to compile. A reader can copy the block into a file and run it.

```php
<?php

declare(strict_types=1);

use TinyBlocks\Outbox\DoctrineOutboxRepository;
use TinyBlocks\Outbox\Serialization\PayloadSerializerReflection;
use TinyBlocks\Outbox\Serialization\PayloadSerializers;

# Single-line comments use #.
$repository = new DoctrineOutboxRepository(
    connection: $connection,
    payloadSerializers: PayloadSerializers::createFrom(elements: [
        new PayloadSerializerReflection()
    ])
);
```

**Inline fragment examples** have at most 3 lines of executable code, no `use` statements, and no
type declarations. Fragments may omit the prologue.

```php
Code::OK->value;
```

The criteria are mechanical: a block meeting any self-contained condition gets the prologue. A
block meeting every fragment condition may omit it. There is no middle ground.

The `#` convention for inline comments applies only to code examples inside Markdown files. PHP
files under `src/` and `tests/` have no inline comments at all, except `# TODO: <reason>` (see
rule 16 in `php-library-code-style.md`).

### FAQ

FAQ entries are numbered with zero-padded prefixes and end with a question mark:

```markdown
### 01. Why is DomainEvent close to a marker interface?

A domain event is a fact about something that happened in the domain. The contract carries only
`revision()` so the library can route schema migrations through upcasters.

> Vaughn Vernon, *Implementing Domain-Driven Design* (Addison-Wesley, 2013), Chapter 8,
> "Domain Events".
```

Bibliographic citations follow `> Author, *Title* (Publisher, Year), Chapter X, "Section Name".`
The chapter and section fragments are optional when the title is precise enough. Multiple
citations stack as separate blockquote lines.

### License and Contributing

```markdown
## License

<LibName> is licensed under [MIT](LICENSE).
```

```markdown
## Contributing

Please follow the [contributing guidelines](https://github.com/tiny-blocks/tiny-blocks/blob/main/CONTRIBUTING.md) to
contribute to the project.
```

## Structured data

Tables are preferred to prose for any structured information: constructor parameter lists,
builder method catalogs, default value tables, complexity tables, and configuration matrices.
Column layout is chosen per case. No fixed column set is mandated.

## Required repository files

In addition to the README, every library repository contains the files below. Their canonical
bodies are the drop-in assets in the `tiny-blocks-create` skill. This rule only asserts they
must exist and match those assets.

- `SECURITY.md`: security policy (supported versions, private reporting via GitHub Security
  Advisories). `<lib-name>` is substituted.
- `.github/ISSUE_TEMPLATE/bug_report.md`: bug report template (`labels: bug`).
- `.github/ISSUE_TEMPLATE/feature_request.md`: feature request template (`labels: enhancement`).
- `.github/PULL_REQUEST_TEMPLATE.md`: pull request template linking the centralized contributing
  guidelines, with the standard checklist (`composer review` passes, `composer tests` passes).
