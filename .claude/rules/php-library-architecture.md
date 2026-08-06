---
description: Folder structure, public API boundary, and Internal/ semantics for PHP libraries.
paths:
    - "src/**/*.php"
---

# Architecture

Covers the physical layout of the library. Folder structure, the boundary between public API and
implementation detail, and where each type of class lives. Semantic rules (value objects,
exceptions, enums, complexity, nomenclature) live in `php-library-modeling.md`. Code style lives
in `php-library-code-style.md`.

## Pre-output checklist

Verify every item before producing or relocating any file. If any item fails, revise before
outputting.

1. None of the following folder names exist in `src/`: `Models/`, `Entities/`, `ValueObjects/`,
   `Enums/`, `Domain/`. They carry no semantic content and conflate technical role with domain
   meaning.
2. The `src/` root contains only interfaces, extension points, public enums, thin orchestration
   classes, and primary implementations or façades. Substantial logic (algorithms, state machines,
   I/O) lives in `src/Internal/`, never at the root.
3. `src/Internal/` is implementation detail and not part of the public API. Breaking changes
   inside `src/Internal/` are not semver-breaking.
4. Consumers must not reference, extend, or depend on any type inside `src/Internal/`. The
   namespace itself is the boundary.
5. Public exception classes live in `src/Exceptions/`.
6. Internal exception classes live in `src/Internal/Exceptions/`.
7. Public enums live at the `src/` root or inside a public `<ConceptGroup>/` folder. Enums used
   only by internals live in `src/Internal/`.
8. Public interfaces live at the `src/` root or inside a public `<ConceptGroup>/` folder.
9. A `<ConceptGroup>/` folder at the `src/` root groups related public types under a shared
   concept. Each group has its own namespace and is part of the public API.
10. `<ConceptGroup>/` is optional. Use it only when the library exposes several coherent groups of
    types (for example, aggregates and events) rather than a flat set of types around a single
    concept.
11. Test fixtures representing domain concepts live in `tests/Models/`. Test doubles for system
    boundaries live at the root of `tests/Unit/` or `tests/Integration/`. No dedicated `Mocks/`
    or `Doubles/` subdirectory exists. Vendor compatibility (driver) tests, verifying the
    library against specific external libraries/frameworks, are optional and have no `src/`
    counterpart. They exist only as tests, under `tests/Integration/Drivers/<Vendor>/`,
    grouped by vendor. Never a top-level `Drivers/` under `tests/`.
12. The `tests/Integration/` folder exists only when the library interacts with external
    infrastructure (filesystem, database, network). Otherwise, the folder is absent.

## Folder structure

Canonical layout for a PHP library in the tiny-blocks ecosystem.

```
src/
├── <PublicInterface>.php     # public contract at root
├── <Implementation>.php      # main implementation or extension point at root
├── <PublicEnum>.php          # public enum at root
├── <ConceptGroup>/           # public folder grouping related public types under a shared concept
│   ├── <PublicType>.php
│   └── ...
├── Internal/                 # implementation details, not part of the public API
│   ├── <Collaborator>.php
│   └── Exceptions/           # internal exception classes
└── Exceptions/               # public exception classes

tests/
├── Models/                   # domain fixtures reused across tests
├── Unit/                     # unit tests targeting the public API
│   ├── <SomeMock>.php        # test doubles at root of Unit/
│   └── <SomeSpy>.php
└── Integration/              # only present when the library interacts with infrastructure
    ├── Drivers/              # only present when the library exposes vendor-specific drivers
    │   └── <Vendor>/         # tests against one specific third-party implementation
    └── <SomeMock>.php        # test doubles at root of Integration/ when needed
```

Never use `Models/`, `Entities/`, `ValueObjects/`, `Enums/`, or `Domain/` as folder names. They
carry no semantic content and describe technical role instead of domain meaning.

## Public API boundary

The `src/` root is the contract. Everything at the root, plus everything inside public
`<ConceptGroup>/` folders and the public `Exceptions/` folder, is what consumers depend on. Changes
to these types follow semver rules.

`src/Internal/` is implementation detail. The namespace itself signals the boundary. Consumers
must not depend on any type inside `src/Internal/`. Breaking changes inside `src/Internal/` are
not semver-breaking for the library.

### What lives at the public boundary

- Interfaces that define contracts for consumers.
- Extension points designed to be subclassed or composed by consumers.
- Public enums and value objects consumers manipulate directly.
- Thin orchestration classes that wire collaborators together without containing substantial logic.
- Public exception classes consumers may catch.

### What lives in `src/Internal/`

- Algorithms, state machines, and complex transformations.
- Adapters for I/O (filesystem, network, database).
- Collaborators that exist purely to break a public class into testable units.
- Implementation details that may change between minor or patch releases.
- Internal exception classes raised by collaborators.

## Reference examples

### Small library with flat root

```
src/
├── Timezone.php              # public value object
├── Timezones.php             # public collection
├── Clock.php                 # public interface
└── Internal/
    ├── SystemClock.php       # default Clock implementation
    └── Exceptions/
        └── InvalidTimezone.php
```

Everything lives at the root or inside `Internal/`. No `<ConceptGroup>/` folders. Suitable when
the library exposes a small, cohesive set of types around a single concept.

### Library with public concept groups

```
src/
├── ValueObject.php                 # public extension point at root
├── Aggregate/                      # public namespace grouping aggregate types
│   ├── AggregateRoot.php
│   ├── EventualAggregateRoot.php
│   └── ModelVersion.php
├── Event/                          # public namespace grouping event types
│   ├── EventRecord.php
│   ├── EventRecords.php
│   └── SequenceNumber.php
├── Internal/
│   ├── DefaultModelVersionResolver.php
│   └── Exceptions/
│       └── InvalidSequenceNumber.php
└── Exceptions/
    └── EventRecordingFailure.php
```

`Aggregate/` and `Event/` are public folders at the root, each grouping a coherent set of public
types under one shared concept. Consumers import directly, for example
`TinyBlocks\<LibName>\Aggregate\AggregateRoot`. Suitable when the library exposes several distinct
concept areas, each with its own set of related types.
