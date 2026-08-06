---
description: Semantic modeling rules for PHP libraries (nomenclature, value objects, exceptions, enums, extension points, complexity).
paths:
    - "src/**/*.php"
---

# Modeling

Library modeling rules. How to model the concepts the library exposes. Folder structure and
public API boundary live in `php-library-architecture.md`. Code style lives in
`php-library-code-style.md`. Tooling lives in `php-library-tooling.md`.

## Pre-output checklist

Verify every item before producing any PHP code that defines a model, an exception, or an
algorithm. If any item fails, revise before outputting.

1. Each model has a single, clear responsibility. Apply DDD, SOLID, DRY, and KISS where they
   sharpen the design, not as dogma.
2. Concept names. Every class, property, method, and exception name reflects the concept the
   library represents, not a technical role.
3. No always-banned names. Never use `Data`, `Info`, `Utils`, `Item`, `Record`, `Entity` as
   class suffix, prefix, or method name. Never use `Exception` as a class suffix. Exception:
   names that correspond to externally standardized identifiers (HTTP status text from RFC
   documents, PSR interface names being mirrored, etc.) are permitted. The standard reference
   is the meaning carrier.
4. No anemic verbs as the primary operation name (`ensure`, `validate`, `check`, `verify`,
   `assert`, `mark`, `enforce`, `sanitize`, `normalize`, `compute`, `transform`, `parse`) unless
   the verb is the library's reason to exist.
5. Architectural role names (`Manager`, `Handler`, `Processor`, `Service`, and their verb forms
   `process`, `handle`, `execute`) are allowed only when the class IS that role for consumers
   integrating with the library.
6. Value objects are immutable. No setters. Operations return new instances.
7. Value objects compare by value, never by reference. No identity field.
8. Value objects validate invariants in the constructor and throw a dedicated exception on
   invalid input.
9. Value objects with multiple creation paths use static factory methods (`from`, `of`, `zero`)
   with a private constructor.
10. Every failure throws a dedicated exception class named after the invariant it guards. Never
    `throw new DomainException(...)`, `throw new InvalidArgumentException(...)`, or any other
    generic native exception directly.
11. Dedicated exception classes extend the appropriate native PHP exception (`DomainException`,
    `InvalidArgumentException`, `OverflowException`, etc.).
12. Exceptions are pure. No transport-specific fields (HTTP status in `code`, formatted message
    for end-user display). They signal invariant violations only, never control flow.
13. Enums are PHP backed enums. They include methods only when those methods carry vocabulary
    meaning. A value or behavior a case owns lives on the enum as that method, called instead of a
    `match` on the case at the site. See "Polymorphism and tell-don't-ask" in
    `php-library-code-style.md`.
14. Extension points use `class` instead of `final readonly class`. They expose a private
    constructor with static factory methods as the only creation path. Internal state is
    injected via the constructor.
15. Algorithms run in O(N) or O(N log N) unless the problem inherently requires worse. O(N²)
    or worse needs explicit justification.
16. Prefer lazy or streaming evaluation over materializing intermediate results. Memory usage
    is bounded and proportional to the output, not to the sum of intermediate stages.
17. A configuration-like value object whose fields are mostly optional exposes a no-argument
    baseline factory (`default()`) plus fluent immutable `with*` copies, not a single factory
    whose signature lists every field. See "Value objects".

## Modeling principles

Apply the following principles where they sharpen the design. Treat them as guides, not as dogma.

- Single responsibility. Each model represents one concept, has one reason to change, and
  exposes operations that belong to that concept.
- DDD ubiquitous language. Names, types, and operations match the vocabulary the library's
  domain uses. Code and conversation share the same terms.
- SOLID. Interfaces define narrow contracts. Composition is preferred to inheritance.
  Substitutability holds at every interface boundary.
- DRY. No duplicated logic across two or more places. See "Duplication" in
  `php-library-code-style.md` for how to resolve it without inheritance or private helpers.
- KISS. No abstraction without real duplication or isolation need.

## Nomenclature

- Every class, property, method, and exception name reflects the concept the library represents.
  A math library uses `Precision` and `RoundingMode`. A money library uses `Currency` and
  `Amount`. A collection library uses `Collectible` and `Order`.
- Name classes after what they represent, not after what they do technically. Use `Money`,
  `Color`, `Pipeline`, not `MoneyCalculator`, `ColorHelper`, `PipelineProcessor`.
- Name methods after the operation in the library's vocabulary. Use `add()`, `convertTo()`,
  `splitAt()`, not `compute()`, `process()`, `handle()`.

### Always banned

These names carry zero semantic content. Never use them anywhere as class suffix, prefix, or
method name.

- `Data`, `Info`, `Utils`, `Item`, `Record`, `Entity`.
- `Exception` as a class suffix (e.g., `FooException`). Use the invariant name when extending a
  native exception (e.g., `PrecisionOutOfRange`, not `InvalidPrecisionException`).

### Externally standardized names (exception to the banlist)

Names that correspond to externally standardized identifiers are exempt from the banlist. The
standard reference is the meaning carrier. Renaming weakens it. Examples:

- HTTP status text from RFC documents (`unprocessableEntity` from RFC 4918, `noContent`).
- PSR interface names being mirrored as test doubles (`ClientException` mirroring
  `Psr\Http\Client\ClientExceptionInterface`).
- Unicode category names, locale identifiers, MIME type tokens, and similar registered names.

This exception applies only when the external standard is the actual source of the name. It
does not authorize using `Data` or `Entity` as generic suffixes when no external reference is
involved.

### Anemic verbs

These verbs hide what is actually happening behind a generic action. Banned unless the verb IS
the operation that constitutes the library's reason to exist (e.g., a JSON parser may have
`parse()`, a hashing library may have `compute()`).

- `ensure`, `validate`, `check`, `verify`, `assert`, `mark`, `enforce`, `sanitize`, `normalize`,
  `compute`, `transform`, `parse`.

When in doubt, prefer the domain operation name. `Password::hash()` beats `Password::compute()`.
`Email::parse()` is fine in a parser library but suspicious elsewhere. Use `Email::from()`
instead.

### Architectural roles

These names describe a role the library offers as a building block. Acceptable when the class IS
that role (e.g., `EventHandler` in an events library, `CacheManager` in a cache library,
`Upcaster` in an event-sourcing library). Not acceptable on domain objects inside the library
(value objects, enums, contract interfaces).

- `Manager`, `Handler`, `Processor`, `Service`.
- Verb forms: `process`, `handle`, `execute`.

The test. If the consumer instantiates or extends this class to integrate with the library, the
role name is legitimate. If the class models a concept the consumer manipulates (a money amount,
a country code, a color), the role name is wrong.

**Scope.** The architectural-role banlist and the anemic-verb banlist apply to the **public
surface**: types at the `src/` root, types in public `<ConceptGroup>/` folders, and public
exception and contract names. Inside `src/Internal/` (implementation detail by definition, where
the namespace is the boundary), a collaborator may carry a mechanical role or operation name that
describes its job (`Decoder`, `Encoder`, `Parser`, `Resolver`), since consumers never see or
manipulate it. The always-banned names (`Data`, `Info`, `Utils`, `Item`, `Record`, `Entity`)
remain banned everywhere, `Internal/` included.

## Value objects

- Are immutable. No setters. No mutation after construction. Operations return new instances.
- Compare by value, not by reference.
- Validate invariants in the constructor and throw a dedicated exception on invalid input.
- Have no identity field.
- Use static factory methods (`from`, `of`, `zero`) with a private constructor when multiple
  creation paths exist. The factory name communicates the semantic intent.

**Prohibited.** Public constructor with multiple creation paths. Semantics are unclear at the
call site:

```php
final readonly class Money
{
    public function __construct(public int $amount, public Currency $currency) {}
}

new Money(amount: 1000, currency: Currency::BRL);
new Money(amount: 0, currency: Currency::USD);
```

**Correct.** Private constructor with named factory methods. Each factory name communicates
intent:

```php
final readonly class Money
{
    private function __construct(public int $amount, public Currency $currency) {}

    public static function of(int $amount, Currency $currency): Money
    {
        return new Money(amount: $amount, currency: $currency);
    }

    public static function zero(Currency $currency): Money
    {
        return new Money(amount: 0, currency: $currency);
    }
}

Money::of(amount: 1000, currency: Currency::BRL);
Money::zero(currency: Currency::USD);
```

When a value object is configuration-like and most of its fields are optional with defaults, prefer
a baseline factory that takes no required arguments (`default()`, or `from()` with every parameter
defaulted) together with fluent immutable `with*` copies, over a single factory whose signature
carries every field. Each `with*` returns a new instance. Prefer the `with*` methods on the value
object itself over a separate mutable builder class: the value object is already immutable, so it
is its own builder. The smell is a factory signature that lists every field while most are
optional.

**Prohibited.** A single factory whose signature carries every field, most of them optional:

```php
MoneyFormat::from(scale: 4, symbol: '€', grouping: ',');
```

**Correct.** A baseline `default()` plus fluent `with*` copies that override only what differs:

```php
MoneyFormat::default()->withScale(scale: 4)->withGrouping(grouping: ',');
```

## Exceptions

- Every failure throws a dedicated exception class named after the invariant it guards. Never
  `throw new DomainException(...)`, `throw new InvalidArgumentException(...)`,
  `throw new RuntimeException(...)`, or any other generic native exception directly. If the
  invariant is worth throwing for, it is worth a named class.
- Dedicated exception classes extend the appropriate native PHP exception (`DomainException`,
  `InvalidArgumentException`, `OverflowException`, etc.). The native class is the parent, never
  the thing that is thrown. Consumers that catch the broad standard types continue to work.
  Consumers that need precise handling can catch the specific classes.
- Exceptions are pure. No transport-specific fields (`code` populated with HTTP status,
  formatted `message` meant for end-user display). Formatting to any transport happens at the
  consumer's boundary, not inside the library.
- Exceptions signal invariant violations only, not control flow.
- Name the class after the invariant violated, never after the technical type. Use
  `PrecisionOutOfRange`, not `InvalidPrecisionException`. Use `CurrencyMismatch`, not
  `BadCurrencyException`. Use `ContainerWaitTimeout`, not `TimeoutException`.
- A descriptive `message` argument is allowed and encouraged when it carries debugging context
  (the violating value, the boundary crossed, the state the library was in). The class name
  identifies the invariant. The message describes the specific violation for stack traces and
  test assertions. Keep messages short, factual, and in American English.

**Prohibited.** Throwing a native exception directly:

```php
if ($value < 0) {
    throw new InvalidArgumentException('Precision cannot be negative.');
}
```

**Correct.** Dedicated class, no message (class name is sufficient):

```php
final class PrecisionOutOfRange extends InvalidArgumentException
{
}

if ($value < 0) {
    throw new PrecisionOutOfRange();
}
```

**Correct.** Dedicated class with debugging context in the message:

```php
if ($value < 0 || $value > 16) {
    $template = 'Precision must be between 0 and 16, got %d.';

    throw new PrecisionOutOfRange(message: sprintf($template, $value));
}
```

## Enums

- Are PHP backed enums.
- Include methods only when those methods carry vocabulary meaning. Examples are
  `OrderStatus::isFinal()` and `RoundingMode::apply()`.
- A value or behavior a case owns (a token, a flag, a derived value) is one of those vocabulary
  methods, a predicate `isXxx()` or a method returning the value, called at the site instead of a
  `match` comparing the case. This is the enum form of tell-don't-ask. See "Polymorphism and
  tell-don't-ask" in `php-library-code-style.md`.

## Extension points

- A class designed to be extended by consumers (e.g., `Collection`, `ValueObject`) uses `class`
  instead of `final readonly class`. All other classes use `final readonly class`. See
  "Inheritance and constructors" in `php-library-code-style.md`.
- Extension point classes use a private constructor with static factory methods (`createFrom`,
  `createFromEmpty`) as the only creation path.
- Internal state is injected via the constructor and stored in a `private readonly` property.

## Time and space complexity

- Algorithms run in O(N) or O(N log N) unless the problem inherently requires worse. O(N²) or
  worse needs explicit justification at the point of definition.
- Prefer lazy or streaming evaluation over materializing intermediate results. In pipeline-style
  libraries, fuse stages so a single pass suffices over the input.
- Memory usage is bounded and proportional to the output, not to the sum of intermediate stages.
- Never re-iterate the same source. When a sequence is consumed once, use lazy creation
  primitives (`createLazyFrom`) instead of materializing.

**Prohibited.** Eager pipeline that materializes between stages:

```php
$paidTotals = array_map(
    static fn(Order $order): float => $order->total(),
    array_filter(
        $orders->toArray(),
        static fn(Order $order): bool => $order->isPaid()
    )
);
```

Each stage allocates a full intermediate array. Memory grows with the input size, even when only
the final scalar matters.

**Correct.** Fused pipeline that runs in a single pass:

```php
$paidTotals = $orders
    ->filter(predicates: static fn(Order $order): bool => $order->isPaid())
    ->map(transformations: static fn(Order $order): float => $order->total())
    ->toArray(keyPreservation: KeyPreservation::DISCARD);
```

Operations stack on the same iterator. No intermediate array is built. Memory stays bounded by
the final output.
