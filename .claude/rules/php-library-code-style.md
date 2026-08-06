---
description: Semantic code rules for all PHP files in libraries.
paths:
    - "src/**/*.php"
    - "tests/**/*.php"
---

# Code style

Semantic rules for all PHP files in libraries. Formatting and structural rules are enforced by
`phpcs.xml` (the `PSR12` ruleset plus curated Squiz, Generic, PSR2, and `SlevomatCodingStandard`
sniffs). Three formatting rules the ruleset does not cover (single-line signatures within 120
characters, vertical alignment of `=>` in multi-line match arms and array literals, no trailing
comma in multi-line lists) are documented at the end of this file under "Formatting overrides".
Single spacing between a type hint and its parameter is mechanically enforced by the
`Squiz.Functions.FunctionDeclarationArgumentSpacing` sniff. Complexity rules live in `php-library-modeling.md`.
Folder structure, public API boundary, and the semantics of `Internal/` live in
`php-library-architecture.md`.

## Pre-output checklist

Verify every item before producing any PHP code. If any item fails, revise before outputting.

1. `declare(strict_types=1)` is present.
2. All parameters, return types, and properties have explicit types.
3. Constructor property promotion is used.
4. Named arguments are used at call sites for own code, tests, and third-party library methods
   (for example, tiny-blocks). Never use named arguments on:
    - Native PHP functions (`array_map`, `in_array`, `preg_match`, `is_null`,
      `iterator_to_array`, `sprintf`, `implode`, and similar).
    - Native PHP enum methods (`from`, `tryFrom`, `cases`).
    - PHPUnit assertions and expectations (`assertEquals`, `assertSame`, `assertTrue`,
      `expectException`, and similar).
    - Interfaces from PHP-FIG PSR standards (PSR-7 `withHeader`, PSR-18 `sendRequest`, etc.).
      The PSR contract does not include parameter names. Implementations may rename parameters.
    - Calls that include variadic spread (`...$args`). PHP rejects positional argument unpacking
      after named arguments. When the caller passes through a `...$variadic`, all arguments are
      positional. New own-code APIs should prefer a typed collection parameter over a variadic
      so named-argument call sites remain possible.
    - Native PHP class static and instance methods (`DateTimeImmutable::createFromFormat`,
      `DateTimeImmutable::createFromInterface`, `->setTimezone`, `->format`, and similar). Their
      parameter names are an internal implementation detail, not a stable contract, exactly as
      with native functions.

   Native PHP **class constructors** (`parent::__construct` calls to `\Exception`,
   `\RuntimeException`, `\InvalidArgumentException`, `\LogicException`, and similar) are not
   in the list above. They accept named arguments, and rule 8 requires using them whenever
   the positional call would pass an argument whose value equals the parameter's default.
   Example: `parent::__construct(message: sprintf(...), previous: $previous)` instead of
   `parent::__construct(sprintf(...), 0, $previous)`. The exclusion above covers native
   functions, enum methods, and native class static and instance methods, but not native class
   constructors (instantiation): those accept named arguments per rule 8.
5. Classes follow the rules in "Inheritance and constructors". `final readonly` is the default,
   with documented exceptions for extension points and for parents that are not `readonly`.
6. Members are ordered constants first, then constructor, then static methods, then instance
   methods. Within each group, order by **member name length ascending** (count the name only,
   without parentheses, arguments, or return type). Constants, enum cases, and methods share
   the same name-length-ascending rule, applied within their respective groups. This mirrors
   the rule that governs constructor parameters and named arguments (rule 7). When two names
   have equal length, order them alphabetically. This ordering may be overridden only when the
   alternative carries explicit documentation value: grouping by domain class with section
   markers (HTTP status codes by 1xx/2xx/3xx/etc), mirroring the order of an implemented
   interface, or similar evident structure. The override must be obvious at first reading.

   **At call sites** (chained method calls in production code, tests, or documentation
   examples), consecutive method invocations on the same receiver are ordered by **method name
   length ascending**, the same rule that governs member declarations. Boolean toggles such as
   `->secure()` and `->httpOnly()` come before parameterized `with*` builders because their
   names are shorter, not because the expression is narrower. When two method names have equal
   length, order them alphabetically.

   **Terminal methods that change the receiver type** stay at the end of the chain regardless
   of name length. A `build()` that returns the built value, a `commit()` that finalizes a unit
   of work, a `send()` that flushes a request, are terminal: the chain ends with them. The
   ordering rule applies only to consecutive calls on the same receiver type. Calls that
   transition to a different type are not reorderable. The same applies in reverse to the
   factory or accessor that starts the chain (`Cookie::create(...)`, `$repository`) stays
   at its position.

   **PHPUnit test classes** follow a dedicated sub-grouping inside the instance-methods group
   that overrides the name-length-ascending rule:

    1. **Lifecycle hooks** first, in PHPUnit execution order:
       `setUpBeforeClass` → `setUp` → `tearDown` → `tearDownAfterClass`. Only those actually
       defined appear. Never introduce an empty hook to satisfy the rule.
    2. **Test methods** (prefix `test`) next, ordered by name length ascending (alphabetical
       tiebreak).
    3. **Data providers** last, ordered by name length ascending (alphabetical tiebreak).

   A method is a data provider if and only if its name appears as the string argument of a
   `#[DataProvider('<name>')]` attribute or a `@dataProvider <name>` docblock annotation on a
   test method in the same class. The naming convention (`*DataProvider`) is informational
   only. The reference is the authoritative signal. A method named `*DataProvider` that no
   test references is dead code under rule 17, not a data provider.
7. Constructor parameters are ordered by parameter name length ascending (count the name only,
   without `$` or type), except when parameters have an implicit semantic order (for example,
   `$start/$end`, `$from/$to`, `$startAt/$endAt`), which takes precedence. Parameters with default
   values go last, regardless of name length. The same rule applies to named arguments at call
   sites. Example order: `$id` (2), `$value` (5), `$status` (6), `$precision` (9).
8. Never pass an argument whose value equals the parameter's default. Omit the argument entirely.
   Example with `toArray(KeyPreservation $keyPreservation = KeyPreservation::PRESERVE)`. The call
   `$collection->toArray(keyPreservation: KeyPreservation::PRESERVE)` becomes
   `$collection->toArray()`. Only pass the argument when the value differs from the default.
9. No `else` or `else if` exists anywhere. Use early returns, polymorphism, or map dispatch
   instead. See "Polymorphism and tell-don't-ask".
10. No abbreviations appear in identifiers. Use `$index` instead of `$i`, `$account` instead of
    `$acc`.
11. No generic identifiers exist. Use domain-specific names instead. Examples are `$data` to
    `$payload`, `$value` to `$totalAmount`, `$item` to `$element`, `$info` to `$currencyDetails`,
    `$result` to `$conversionOutcome`. **Exception:** a factory or constructor parameter that
    wraps a single opaque scalar the value object exists to represent may keep `$value` when no
    more specific meaning applies (for example, `Seconds::from(int $value)`). Where a more
    specific meaning exists, prefer it (`$iso`, `$identifier`, `$isoDay`).
12. No raw arrays exist where a typed collection or value object is available. When data is
    `Collectible`, use the `tiny-blocks/collection` fluent API (`Collection`, `Collectible`). Use
    `createLazyFrom` when elements are consumed once. Raw arrays are acceptable only for primitive
    configuration data, variadic pass-through, and interop at system boundaries. See "Collection
    usage" for the full rule and example.
13. No private methods exist except for private constructors in factory patterns, methods inside
    `src/Internal/` (implementation detail by definition, where the namespace is the abstraction
    boundary), and `setUp` or `tearDown` overrides in PHPUnit test classes. Outside these cases,
    inline trivial logic at the call site or extract it to a collaborator or value object.
14. No logic is duplicated across two or more places (DRY). See "Duplication" for the resolution
    under the inheritance and private-method constraints.
15. No abstraction exists without real duplication or isolation need (KISS).
16. No inline comments exist in `src/` or `tests/`, except `# TODO: <reason>` when implementation
    is unknown, uncertain, or intentionally deferred. Code is the documentation. Block comments
    (`/* */`) never appear outside docblocks (`/** */`). The `#` style for inline PHP comments
    applies only to code examples inside Markdown files (see `php-library-documentation.md`).
17. No dead or unused code exists. Remove unreferenced classes, methods, constants, and imports.
18. Never create public methods, constants, or classes in `src/` solely to serve tests. If
    production code does not need it, it does not exist.
19. Format strings with placeholders (`%s`, `%d`, `%f`, etc.) are assigned to a `$template`
    variable before being passed to `sprintf`. The variable assignment and the `sprintf` call live
    on separate statements. See "Format strings" for examples.
20. All class references use `use` imports at the top of the file. Fully qualified names inline are
    prohibited.
21. Return types and `new` calls use the explicit class name. `self` is prohibited as a type,
    as a return type, in `new self()` instantiation, and in static method calls
    (`self::from(...)` → `ClassName::from(...)`). Constant access via `self::CONST_NAME` is the
    only permitted `self::` form. `static` is permitted only inside extension-point classes
    (declared `class` without `final readonly`) and inside traits, where late static binding lets
    subclasses or consuming classes instantiate the correct concrete type. In every other
    context, use the class name.
22. Always use the most current and clean syntax available in the target PHP version. Prefer
    `match` over `switch`, first-class callables over `Closure::fromCallable()`, readonly promotion
    over manual assignment, enum methods over external switch or if chains, named arguments over
    positional ambiguity (except where excluded by rule 4), `Collection::map` over foreach
    accumulation, concise standard regex character classes (`\w`, `\d`, `\s`, and their negations)
    over their explicit equivalents (`[A-Za-z0-9_]`, `[0-9]`), and **unparenthesized constructor
    chaining** (PHP 8.4+): `new Foo()->bar()` instead of `(new Foo())->bar()`. The parentheses
    around the `new` expression are no longer required and add visual noise.
23. All identifiers, comments, and documentation use American English. See "American English" for
    the spelling list.
24. No method has more than three `return` statements. This bounds branching complexity and
    coexists with rule 9 (no `else`): early-return guard clauses are fine, but a method that needs
    more than three exit points is doing too much. Invariant violations `throw` a dedicated
    exception rather than returning, so guards rarely add return points. When branching still
    produces more than three returns, replace it with a `match` or map dispatch that resolves to a
    single return, or extract a collaborator. When the branches turn on the runtime type of
    polymorphic collaborator, the behavior belongs on that type instead. See "Return statements"
    and "Polymorphism and tell-don't-ask".
25. The string concatenation operator (`.`) is never used, in any position. A string that
    would be assembled by concatenation, whether it embeds a value or joins two or more
    strings, is built with `sprintf` and a `$template` variable (rule 19) instead. This
    covers value prefixes, value suffixes, inline fragments, and plain joins. See "Format
    strings".

    **Exception:** a `const` string literal that contains no `sprintf` placeholder may
    use `.` to split a message across lines when a single-line literal would exceed the
    120-character limit. In that case `sprintf` offers no benefit, since the `$template`
    line would itself exceed the limit, and heredoc and nowdoc are not permitted in
    constant expressions, so concatenation is the only way to honor the line length.
    This exception is limited to placeholder-free constant literals. Runtime string
    assembly, and any constant that interpolates a value, still uses `sprintf` with a
    `$template`.
26. Behavior that varies by the concrete type of type the library owns is a polymorphic method
    on that type, never an `instanceof`, `get_class`, or enum-case branch. A value or behavior an
    enum case owns (a token, a flag about the case's nature, a derived value) lives on the enum as
    a predicate or vocabulary method, called at the site instead of comparing the case. Behavior
    that depends on a collaborator's state lives on that collaborator. See "Polymorphism and
    tell-don't-ask".

## Naming

- Internal code (variables, methods, classes) uses `camelCase`.
- Constants and enum-backed values when representing codes use `SCREAMING_SNAKE_CASE`.
- Names describe what in domain terms, not how technically. `$monthlyRevenue` instead of
  `$calculatedValue`. Generic technical verbs are avoided. See `php-library-modeling.md` for the
  full banlist of generic and anemic names.
- Booleans use predicate form. Examples are `isActive`, `hasPermission`, `wasProcessed`.
- Collections are always plural. Examples are `$orders`, `$lines`.
- A boolean method reads as a predicate, using an `is`/`has`/`can`/`was`/`should` prefix or a
  third-person verb that reads as a yes/no question, such as `contains`, `matches`, `supports`,
  `equals`, or `omits`.

## Class self-references

Type declarations, return types, and `new` calls inside a class use the explicit class name.
The class name is unambiguous, survives refactors that move the method to a different class,
and reads identically inside the class body and at the call site.

- `self` is prohibited everywhere as a type, as a return type, in `new self()` instantiation,
  and in static method calls (`self::from(...)`). Constant access via `self::CONST_NAME` is
  **permitted** and is the only allowed `self::` form. The prohibition covers the forms that
  carry refactoring ambiguity when a method moves to a different class (type, instantiation, and
  static-call forms): a `self::from()` call rebinds to the wrong class if the method moves,
  exactly like `new self()`. Constant access does not have that ambiguity because the constant is
  declared in the same class body.
- `static` is permitted only inside extension-point classes (declared `class` without
  `final readonly`) and inside traits, where late static binding is required for subclasses or
  consuming classes to instantiate the correct concrete type.
- In every other context (the default `final readonly class`, factory methods, return types),
  use the class name.

**Prohibited.** `self` as return type and `new self()` inside a final class:

```php
final readonly class UserAgent
{
    public static function from(string $product): self
    {
        return new self(product: $product);
    }
}
```

**Correct.** Explicit class name in a final class:

```php
final readonly class UserAgent
{
    public static function from(string $product): UserAgent
    {
        return new UserAgent(product: $product);
    }
}
```

**Correct.** `static` permitted in an extension-point class:

```php
class Collection
{
    public static function createFrom(iterable $elements): static
    {
        return new static(elements: $elements);
    }
}
```

## Inheritance and constructors

- All classes are `final readonly` by default.
- Use `class` (without `final` or `readonly`) only when the class is designed as an extension point
  for consumers, for example `Collection` or `ValueObject`.
- Use `final class` without `readonly` only when the parent class is not readonly, for example
  when extending a third-party abstract class.
- Use `final class` without `readonly` is also permitted for `src/Internal/` collaborators that
  carry intrinsically mutable state (resource handles, counters, cursors) where the mutation is
  central to the class's responsibility (`Stream` closing a resource, `Cursor` advancing a
  position). The class must remain confined to `src/Internal/`.
- Use `final class` without `readonly` for classes that consist exclusively of `static` methods
  (no instance properties, no instance methods, only static factories or utilities). Pair it
  with `private function __construct() {}` to prevent instantiation. `readonly` is meaningless
  without instance state, and the private constructor signals that the class is a static
  surface, not a value type.
- Inheritance between concrete classes is prohibited. Every concrete class is `final`.
- Polymorphism uses interfaces plus composition, never extension of concrete types.
- The only allowed `extends` is against framework or SPL base classes that the language requires.
  Examples are `RuntimeException`, `LogicException`, `PHPUnit\Framework\TestCase`.
- Constructors of `final` classes are `private` when paired with named factory methods, `public`
  otherwise. `protected` constructors are prohibited because no subclasses exist to call them.

## Comparisons

1. Null checks use `is_null($variable)`, never `$variable === null`.
2. Empty string checks on typed `string` parameters use `$variable === ''`. Avoid `empty()` on
   typed strings because `empty('0')` returns `true`.
3. Mixed or untyped checks (value may be `null`, empty string, `0`, or `false`) use
   `empty($variable)`.

## American English

All identifiers, enum values, comments, and error codes use American English spelling. Examples
are `canceled` (not `cancelled`), `organization` (not `organisation`), `initialize` (not
`initialise`), `behavior` (not `behaviour`), `modeling` (not `modelling`), `labeled` (not
`labelled`), `fulfill` (not `fulfil`), `color` (not `colour`).

## PHPDoc

### When required

Everything exposed on the public API for consumption carries PHPDoc per these rules.

- Every method of an interface, regardless of location. Interfaces are contracts, so they carry
  PHPDoc per these rules even when declared inside `src/Internal/`.
- Every public method of a concrete class outside `src/Internal/`. Public classes are at the
  public API boundary by definition. Consumers call every public method directly, and the
  PHPDoc is the contract for each call. Trivial getters and `with*` methods are not exempt.
  The only exception is a public method whose contract is already documented on an implemented
  interface (the interface carries the docblock).
- Every abstract method on a public class or extension point outside `src/Internal/`. Abstract
  methods are part of the public contract consumers implement or override, so each carries PHPDoc
  exactly as an interface method does.
- A class-level summary docblock on every interface (including interfaces inside `src/Internal/`)
  and on every public class or enum outside `src/Internal/`. The summary is a single line placed
  directly above the declaration stating what the type is or does, following the same summary-line
  rule as method docblocks. It is the class-level counterpart of the per-method PHPDoc.

### When prohibited

- Constructors. The constructor signature with property promotion is self-documenting. Parameter
  types are already explicit in the signature.
- Private and protected methods.
- Public methods of concrete classes whose contract is already documented on an implemented
  interface. The interface carries the docblock.
- Concrete classes and collaborators inside `src/Internal/`. Internal implementation types are
  detail, not contract, and carry no PHPDoc, class-level summary included. **Interfaces are the
  exception**: an interface declared inside `src/Internal/` is still a contract and follows the
  interface PHPDoc rules under "When required", including the class-level summary. See
  `php-library-architecture.md` for the architectural meaning of `Internal/`.
- Anywhere inside `tests/`. Test methods name the scenario via the `testXxxWhenYyyThenZzz`
  naming convention, and the `@Given`/`@When`/`@Then`/`@And` annotation blocks defined in
  `php-library-testing.md` describe the steps. PHPDoc documentation (summary plus
  `@param`/`@return` descriptions) is prohibited on test methods, data providers, fixtures,
  setUp/tearDown overrides, and anonymous classes inside tests. The BDD annotations are not
  PHPDoc documentation in the sense of this section and remain required per the testing rule.
- Single-line PHPDocs with only a tag (`/** @param ... */`, `/** @return ... */`,
  `/** @throws ... */`). PHPDoc always opens with a summary line. Bare-tag docblocks are
  prohibited regardless of how few tags they carry.

The prohibitions above apply to **every form of PHPDoc** in the prohibited scope:
method-level docblocks, property-level docblocks, inline `@var` annotations on local variables,
and PHPDoc blocks placed above anonymous functions or closures inside method bodies. Inside
`tests/`, zero PHPDoc is the rule, save for the generics carve-out below. Inside `src/Internal/`,
zero PHPDoc applies to concrete classes and collaborators, but interfaces carry PHPDoc per "When
required", and the generics carve-out below still applies to those concrete classes. PHPStan
errors that result from the missing annotations on the non-interface code route through
`ignoreErrors` (see below).

**Generics carve-out.** The prohibitions above are waived for PHPDoc that exists *purely to
express generics* the native type system cannot: `@template`, `@extends`, `@implements`, and the
`@param`/`@return`/`@var` tags whose sole purpose is to carry a type parameter (for example
`Collection<TValue>`, `iterable<TValue>`, `Closure(TValue): bool`, `static<TValue>`). These tags
are permitted wherever they are necessary for generic typing, including on **constructors**, on
**concrete classes and collaborators inside `src/Internal/`**, and as a **bare-tag block with no
summary line** (a summary would be the prohibited descriptive form). The waiver is strict: it
covers only the type-parameter information. Descriptive or redundant PHPDoc (summaries, prose
`@param`/`@return` descriptions, anything restating what the signature already says) stays
prohibited everywhere. When the only missing annotation is non-generic (a plain iterable value
type, a mixed-origin argument), the typed-array case below still applies and routes through
`ignoreErrors`, not PHPDoc.

The PHPDoc prohibitions above take priority over the typed-array case. When PHPStan at
`level: max` flags a missing iterable value type (`missingType.iterableValue`,
`argument.type`, `return.type`):

- On a **constructor parameter** → suppress via `ignoreErrors` in `phpstan.neon.dist`. Do not
  add PHPDoc.
- On a concrete class or collaborator inside **`src/Internal/`** → suppress via `ignoreErrors`.
  Do not add PHPDoc. An interface inside `src/Internal/` is the exception: it carries PHPDoc per
  "When required", so the typed-array information goes in the docblock, not `ignoreErrors`.
- On anything inside **`tests/`** → suppress via `ignoreErrors`. Do not add PHPDoc.
- On a **public method of a public (non-Internal) class** → add full PHPDoc with summary,
  `@param` descriptions, and the typed-array information. The bare-tag form remains
  prohibited. This is the normal case where PHPDoc is permitted by "When required" above.

The summary requirement and the bare-tag prohibition are never waived. Use `ignoreErrors` only
when the context (constructor, `src/Internal/`, `tests/`) makes PHPDoc impossible. Every public
method of a public concrete class carries PHPDoc per "When required", whether the method
has typed-array parameters.

### Style

- Summary on the first line, in domain terms. **Mandatory.** PHPDoc without a summary line is
  prohibited, even when it carries a single `@param` or `@return`.
- Optional detailed body in `<p>` paragraphs below the summary.
- Tags use the form `@param Type $name Description.`, `@return Type Description.`,
  `@throws ExceptionClass If <condition>.`.
- Document `@throws` for every exception the method may raise.
- HTML tags allowed inside descriptions are `<p>` for paragraphs, `<ul><li>` for lists,
  `<code>` for inline code, `<em>` and `<strong>` for emphasis.

### Summary patterns

The summary line is not a creative intent statement. It is a template selected by the method's
name prefix. Apply the matching template. Only methods with no matching prefix require a
free-form one-line summary in domain terms.

| Method shape                                                            | Template                                                                       |
|-------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| Static factory (`create`, `from`, `fromX`, `with*` when static)         | `Creates a {ClassName} from {input}.` or `Builds a {ClassName} with {fields}.` |
| `with*` instance method                                                 | `Returns a copy of the {ClassName} with the {field} replaced.`                 |
| Getter (no prefix, returns a property: `code()`, `body()`, `headers()`) | `Returns the {field}.`                                                         |
| Predicate (`is*`, `has*`, `can*`, `was*`, `should*`)                    | `Tells whether {condition}.`                                                   |
| Converter (`toArray`, `toString`, `asX`)                                | `Returns the {ClassName} as {target shape}.`                                   |
| `apply*`, `merge*`, `add*`, and other side-effect-free operations       | One-line summary in domain terms describing the operation.                     |

The patterns are mandatory when applicable. They make summary lines mechanical: substitute
`{ClassName}` and `{field}` and the summary is complete. No per-method intent decision is
required. Volume is never a reason to skip the summary. Many methods just mean applying the
template many times.

### Cross-references

- `{@see ClassName}` for links to other types in the codebase.
- `@see Author, <em>Title</em> (Publisher, Year), Chapter X.` for bibliographical references.

### Examples

**Prohibited.** Single-line bare-tag PHPDoc, no summary:

```php
/** @param array<string, mixed>|null $body */
public static function with(Code $code, ?array $body = null): Response
```

**Prohibited.** PHPDoc on a constructor:

```php
/** @param array<string, mixed> $entries */
public function __construct(public array $entries)
{
}
```

**Prohibited.** PHPDoc on anything inside `src/Internal/`:

```php
namespace TinyBlocks\Http\Internal\Client;

final readonly class Url
{
    /** @param array<string, scalar>|null $query */
    public static function compose(string $path, ?array $query, string $baseUrl): string
    {
    }
}
```

**Correct.** Generic array type with summary and `@param` description:

```php
/**
 * Builds a synthesized response from a status code and an optional body.
 *
 * @param array<string, mixed>|null $body The response body as an associative array.
 * @return Response The synthesized response instance.
 */
public static function with(Code $code, ?array $body = null): Response
```

**Correct.** Interface with rich description, paragraphs, cross-references, and bibliography:

```php
/**
 * Money tied to a specific currency.
 *
 * <p>Operations between different currencies raise <code>CurrencyMismatch</code>. Arithmetic
 * preserves the currency.</p>
 *
 * <p>Sibling of {@see Quantity}, not a parent. <code>Money</code> carries currency semantics.</p>
 *
 * @see Eric Evans, <em>Domain-Driven Design</em> (Addison-Wesley, 2003), Chapter 5.
 */
interface Money
{
    /**
     * Adds the given amount.
     *
     * @param Money $other The amount to add.
     * @return Money A new instance with the summed amount.
     * @throws CurrencyMismatch If <code>$other</code> has a different currency.
     */
    public function add(Money $other): Money;
}
```

**Correct.** Concrete class with a short summary and direct tags:

```php
/**
 * IANA timezone identifier (e.g. America/Sao_Paulo).
 */
final readonly class Timezone
{
    /**
     * Creates a Timezone from a valid IANA identifier.
     *
     * @param string $identifier The IANA timezone identifier.
     * @return Timezone The created instance.
     * @throws InvalidTimezone If the identifier is not a valid IANA timezone.
     */
    public static function from(string $identifier): Timezone
    {
        # ...
    }
}
```

## Dependencies

When the library needs an external dependency, prefer packages from the `tiny-blocks` ecosystem
(https://github.com/tiny-blocks) whenever a suitable option exists. Reach for outside packages
only when the ecosystem has no equivalent that fits the use case.

## Collection usage

When a property or parameter is `Collectible`, use its fluent API. Never break out to raw array
functions such as `array_map`, `array_filter`, `iterator_to_array`, or `foreach` plus accumulation.
The same applies to `filter()`, `reduce()`, `each()`, and every other `Collectible` operation.
Chain them fluently. Never materialize with `iterator_to_array` to then pass into a raw `array_*`
function.

**Prohibited.** `array_map` plus `iterator_to_array` on a `Collectible`:

```php
$names = array_map(
    static fn(Element $element): string => $element->name(),
    iterator_to_array($collection)
);
```

**Correct.** Fluent chain with `map()` plus `toArray()`:

```php
$names = $collection
    ->map(transformations: static fn(Element $element): string => $element->name())
    ->toArray(keyPreservation: KeyPreservation::DISCARD);
```

## Format strings

When building a message with placeholders, assign the format string to a `$template` variable
first. Pass it to `sprintf` on a separate statement. The format and the data are visually
separated, and the template line stays scannable.

**Prohibited.** Format string inline with the call:

```php
if ($value < 0 || $value > 16) {
    throw new PrecisionOutOfRange(
        message: sprintf('Precision must be between 0 and 16, got %d.', $value)
    );
}
```

**Correct.** Format string in a `$template` variable:

```php
if ($value < 0 || $value > 16) {
    $template = 'Precision must be between 0 and 16, got %d.';

    throw new PrecisionOutOfRange(message: sprintf($template, $value));
}
```

The `.` operator is never used to assemble a string. Value prefixes, value suffixes, inline
fragments, and plain joins all go through `sprintf` with a `$template`. This holds even when
no value is interpolated, for example when joining a directory and a file name.

The sole exception is a placeholder-free `const` string literal that would exceed 120
characters on a single line: it may use `.` to split across lines, since `sprintf` would
not shorten the line and heredoc is unavailable in constant expressions.

**Prohibited.** Concatenation to inject a value:

```php
$candidate = is_int($value) ? '@' . $value : $value;
```

**Correct.** `$template` plus `sprintf`:

```php
$template = '@%d';
$candidate = is_int($value) ? sprintf($template, $value) : $value;
```

**Prohibited.** Concatenation to join strings:

```php
$location = $directory . '/' . $file;
```

**Correct.** A single `$template` for the join:

```php
$template = '%s/%s';
$location = sprintf($template, $directory, $file);
```

## Constructor chaining

PHP 8.4 allows chained method calls directly on a `new` expression without wrapping it in
parentheses. The parentheses are no longer required and only add visual noise. Apply this
everywhere a `new` is followed by a method call.

**Prohibited.** Parentheses around the `new` expression:

```php
$body = (new ServerRequest(uri: 'https://api.example.com', method: 'GET'))
    ->withHeader('Accept', 'application/json')
    ->getBody();
```

**Correct.** No parentheses:

```php
$body = new ServerRequest(uri: 'https://api.example.com', method: 'GET')
    ->withHeader('Accept', 'application/json')
    ->getBody();
```

## Duplication

When two or more places share logic, extract it into a collaborator (a value object, or a class
in `src/Internal/`), or move it onto a collaborator both call sites already depend on. The type
that owns the data owns the derived behavior.

A shared base class is not available: inheritance between concrete classes is prohibited (see
"Inheritance and constructors"). A shared private helper is not available either: private methods
on public classes are prohibited (rule 13). Composition is therefore the only mechanism, and
leaving the duplication in place is never the resolution.

**Prohibited.** The same derivation copied byte for byte into two types:

```php
final readonly class Exam
{
    public function __construct(public int $score) {}

    public function grade(): Grade
    {
        return match (true) {
            $this->score >= 90 => Grade::A,
            $this->score >= 80 => Grade::B,
            $this->score >= 70 => Grade::C,
            default            => Grade::F
        };
    }
}

final readonly class Assignment
{
    public function __construct(public int $score) {}

    public function grade(): Grade
    {
        return match (true) {
            $this->score >= 90 => Grade::A,
            $this->score >= 80 => Grade::B,
            $this->score >= 70 => Grade::C,
            default            => Grade::F
        };
    }
}
```

**Correct.** The derivation lives once on the collaborator both types hold, and each delegates:

```php
final readonly class Score
{
    public function __construct(public int $value) {}

    public function toGrade(): Grade
    {
        return match (true) {
            $this->value >= 90 => Grade::A,
            $this->value >= 80 => Grade::B,
            $this->value >= 70 => Grade::C,
            default            => Grade::F
        };
    }
}

final readonly class Exam
{
    public function __construct(public Score $score) {}

    public function grade(): Grade
    {
        return $this->score->toGrade();
    }
}

final readonly class Assignment
{
    public function __construct(public Score $score) {}

    public function grade(): Grade
    {
        return $this->score->toGrade();
    }
}
```

## Polymorphism and tell-don't-ask

This refines rules 9 and 24. A `match` on an enum, on a scalar, or on a value condition stays
correct. What is prohibited is branching on the runtime type of polymorphic collaborator the
library defines: when behavior differs across the concrete implementations of an interface the
library owns, that behavior is a method on the interface, resolved by the object itself, never an
`instanceof` or `get_class` chain at the call site.

The opening sentence holds only for control flow. When a branch on an enum case yields a value or
behavior that belongs to the case itself, a token, a flag about the case's nature, or a derived
value, that value or behavior is a method on the enum: a predicate `isXxx()`, or a vocabulary
method that returns the value, called at the site instead of comparing the case. Comparing a case
(`$direction === Order::ASCENDING`, `match ($direction)`) stays correct for control flow whose
outcome is not a property of the case. This is the enum form of tell-don't-ask, and the companion
of the modeling rule that enums carry methods only when those methods hold vocabulary meaning (see
`php-library-modeling.md`, "Enums"): a case that drives a derived value is exactly that vocabulary.

A consumer is outside this rule. A consumer matching on a sealed type the library exposes (for
example, translating a parsed tree into its own store) cannot add methods to the library's types,
so its `instanceof` is legitimate. The rule binds the library's own code.

A type the library owns may `instanceof` its own internal types at construction or registration
time, to invoke behavior that exists only on the concrete type and that cannot be lifted onto a
public extension interface without breaking external implementers. The minimal public interface
outweighs the local, build-time type check.

Tell-don't-ask. Behavior that depends on a collaborator's state belongs to the collaborator. Do
not read a collaborator's fields to recompute a result the collaborator should produce. Ask it for
the result, not for its parts. A getter exposes a value the caller needs as data, it is not a
license to reimplement the collaborator's logic at the call site. Tell-don't-ask binds the types
the library owns. Reading a value off a type the library does not own (a dependency's value object,
a PSR type) and computing with it is interop, not a violation: the library cannot add a method to a
type it does not control. The rule still binds the library's own types.

**Prohibited.** Dispatching on the concrete type of interface the library owns:

```php
return match (true) {
    $discount instanceof Percentage => $amount->multiplyBy(factor: $discount->rate()),
    $discount instanceof Fixed      => $amount->subtract(other: $discount->amount())
};
```

**Correct.** The behavior is a method on the interface, resolved by the object:

```php
return $discount->applyTo(amount: $amount);
```

**Prohibited.** Comparing an enum case to produce a value the case owns:

```php
$token = match ($direction) {
    Order::ASCENDING  => '',
    Order::DESCENDING => '-'
};
```

**Correct.** A vocabulary method on the enum returns the value, called at the site:

```php
enum Order: string
{
    case ASCENDING = 'asc';
    case DESCENDING = 'desc';

    public function token(): string
    {
        return match ($this) {
            self::ASCENDING  => '',
            self::DESCENDING => '-'
        };
    }
}

$token = $direction->token();
```

**Prohibited.** Reading a collaborator's parts to recompute what it already owns:

```php
$doubled = Money::of(amount: $price->amount() * 2, currency: $price->currency());
```

**Correct.** Telling the collaborator to produce the result:

```php
$doubled = $price->multiplyBy(factor: 2);
```

## Return statements

A method has at most three `return` statements. The cap keeps methods small and their control
flow scannable, and it complements rule 9: early returns are the preferred alternative to `else`,
but they stop being a simplification once a method accumulates more than three exit points.
Invariant violations are signaled with a `throw`, not a `return`, so guard clauses usually do not
add to the count.

**Prohibited.** Four return points:

```php
public function classify(int $score): Grade
{
    if ($score >= 90) {
        return Grade::A;
    }

    if ($score >= 80) {
        return Grade::B;
    }

    if ($score >= 70) {
        return Grade::C;
    }

    return Grade::F;
}
```

**Correct.** Single return through `match`:

```php
public function classify(int $score): Grade
{
    return match (true) {
        $score >= 90 => Grade::A,
        $score >= 80 => Grade::B,
        $score >= 70 => Grade::C,
        default      => Grade::F
    };
}
```

## Formatting overrides

Three formatting rules are not covered by the canonical `phpcs.xml`. Apply them manually.

### Single-line signatures within 120 characters

A function or constructor signature stays on one line when the whole signature fits within the
120-character limit. Do not break the parameter list onto multiple lines unless the single-line
form would exceed 120 characters. The opening brace still goes on its own line (PSR-12). Break to
one parameter per line only when the signature genuinely overflows.

**Prohibited.** Multiline signature that fits on one line:

```php
private function __construct(
    public ExternalReference $id,
    public Money $amount,
    public OrderContext $context
) {
}
```

**Correct.** Single line within 120 characters:

```php
private function __construct(public ExternalReference $id, public Money $amount, public OrderContext $context)
{
}
```

When the one-line form would exceed 120 characters, break to one parameter per line and apply the
no-trailing-comma rule below. Single spacing between a type hint and its parameter (never padded to
align columns) is enforced mechanically by the `Squiz.Functions.FunctionDeclarationArgumentSpacing`
sniff, so it is not a manual override.

### Vertical alignment of `=>` in match arms and array literals

Multi-line `match` expressions and multi-line array literals with `=>` align the `=>` column
across all arms or entries by padding shorter left-hand sides with spaces. Single-line cases
(one-arm match, single-line array) keep the standard PSR-12 single-space form.

**Prohibited.** Unaligned `=>` in match:

```php
return match ($this) {
    self::MAX_AGE => sprintf($template, $this->value, $value),
    default => $this->value
};
```

**Correct.** Aligned `=>` in match:

```php
return match ($this) {
    self::MAX_AGE => sprintf($template, $this->value, $value),
    default       => $this->value
};
```

**Prohibited.** Unaligned `=>` in array literal:

```php
return [
    'name' => 'Gustavo',
    'role' => 'developer',
    'company' => 'Anthropic'
];
```

**Correct.** Aligned `=>` in array literal:

```php
return [
    'name'    => 'Gustavo',
    'role'    => 'developer',
    'company' => 'Anthropic'
];
```

### No trailing comma in multi-line lists

Never place a trailing comma after the last element of any multi-line list. Applies to parameter
lists, argument lists, array literals, match arms, and every other comma-separated multi-line
structure. PHP accepts trailing commas in these positions, but this ecosystem prohibits them for
visual consistency.

**Prohibited.** Trailing comma after the last argument:

```php
new Precision(
    value: 2,
    rounding: RoundingMode::HALF_UP,
);
```

**Correct.** No trailing comma:

```php
new Precision(
    value: 2,
    rounding: RoundingMode::HALF_UP
);
```
