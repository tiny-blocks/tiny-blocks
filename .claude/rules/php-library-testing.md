---
description: BDD Given/When/Then structure, PHPUnit conventions, fixture rules, and coverage discipline.
paths:
    - "tests/**/*.php"
---

# Testing

PHPUnit conventions for tests in PHP libraries. Covers BDD structure, fixture rules, and coverage
discipline. Code style applies to test files as well. See `php-library-code-style.md`. Folder
structure for `tests/` lives in `php-library-architecture.md`. Canonical thresholds (MSI 100,
covered MSI 100) live in `php-library-tooling.md`.

## Pre-output checklist

Verify every item before producing any test code. If any item fails, revise before outputting.

1. Each test contains exactly one `@When` block. Two actions require two tests.
2. Use `@And` for complementary preconditions or actions within the same scenario, avoiding
   consecutive `@Given` or `@When` tags.
3. Each `@Given` or `@And` block contains exactly one annotation line followed by one expression
   or assignment. Never place multiple variable declarations or object constructions under a
   single annotation. **Exception for data-provider tests.** When the test method binds its
   inputs through a `#[DataProvider]` attribute (or the equivalent `@dataProvider` annotation),
   the `@Given` block may declare the input shape in prose form, without an expression below
   it. The values are bound by PHPUnit before the test body runs, so the prose annotation
   replaces the assignment that would otherwise sit under the `@Given`.

   `@When` blocks follow the same one-expression rule by default: the block represents the
   single action under test. **Exception for repeated-invocation tests** (idempotence, caching,
   memoization). When the purpose of the test is asserting that the same operation produces the
   same outcome across N invocations, the `@When` block may contain N consecutive identical
   invocations, each captured in a numbered variable (`$first`, `$second`, ...), and the
   annotation reads `@When invoked twice` (or thrice, etc.) to make the composite-action
   semantic explicit. Two unrelated actions still require two tests.
4. No intermediate variables used only once. Chain method calls when the intermediate state is
   not referenced elsewhere (e.g., `Money::of(...)->add(...)` instead of
   `$money = Money::of(...)` followed by `$money->add(...)`).
5. No private or helper methods in test classes. The only non-test methods allowed are PHPUnit
   lifecycle hooks (`setUp`, `setUpBeforeClass`, `tearDown`, `tearDownAfterClass`) and data
   providers. Setup logic complex enough to extract belongs in a dedicated fixture class.
6. Test only the public API. Never assert on private state or `Internal/` classes directly.
   One narrow, last-resort exception covers irreducible internal elements. See "White-box
   coverage of irreducible internals".
7. Test the behavior that **raises** an exception, never the exception itself. Exception classes
   represent invariant violations and are value objects, not the subject of behavior tests. A
   test constructs the conditions, invokes the public method that is supposed to fail, and
   asserts the expected exception class is raised (plus its accessor values when they carry
   information relevant to the failure). Constructing an exception directly
   (`new HttpRequestInvalid(...)`) and asserting on its accessors is **prohibited**: the
   exception's structure is exercised through the call path that produces it. If a method does
   not exist whose call path produces the exception, the exception is dead code and should be
   removed.
8. Never mock internal collaborators. Use real objects. Test doubles are used only at system
   boundaries (filesystem, clock, network) when the library interacts with external resources.
9. Name tests after behavior using the `testXxxWhenYyyThenZzz` shape, never after the method
   under test. `Xxx` names the subject or operation, `Yyy` the condition, `Zzz` the expected
   outcome (for example, `testAddMoneyWhenSameCurrencyThenAmountsAreSummed`). The `When`/`Then`
   structure is mandatory. The `@Given`/`@When`/`@Then`/`@And` annotation blocks describe the
   steps within. A condition-free operation may collapse to `testXxxThenZzz` when there is no
   meaningful precondition to name.
10. Use domain-specific names in variables and properties. Never `$spy`, `$mock`, `$stub`,
    `$fake`, `$dummy` as variable or property names. Use the domain concept the object
    represents (`$collection`, `$amount`, `$currency`, `$sortedElements`). Class names like
    `ClientMock` or `GatewaySpy` are acceptable. The variable holding the instance is what matters.
11. Annotations use domain language. Write `/** @Given a collection of amounts */`, not
    `/** @Given a mocked collection in test state */`.
12. Never use the `/** @test */` annotation. Test methods are discovered by the `test` prefix in
    the method name.
13. Named arguments are never used on PHPUnit assertions and expectations. Arguments are passed
    positionally. The canonical rule and its full exclusion list live in
    `php-library-code-style.md` rule 4.
14. Never include conditional logic inside tests. Each `@Then` block expresses one logical
    concept. The only allowed `try`/`catch` is when the assertion target is a property of the
    caught exception that cannot be expressed via `expectException*` methods (notably
    `getPrevious()` for chain inspection). The catch block contains only assertions against the
    caught exception, no branching.
15. Never use `@codeCoverageIgnore`, attributes, or configuration that exclude code from
    coverage. Never suppress mutants via `infection.json.dist` or any other mechanism. See
    "Coverage and mutation discipline".
16. Member ordering in test classes follows `php-library-code-style.md` rule 6 (PHPUnit
    test-class sub-grouping).

## Generics in test PHPDoc

The "zero PHPDoc anywhere inside `tests/`" rule (defined in `php-library-code-style.md`) has one
narrow exception: PHPDoc that exists *purely to express generics* the native type system cannot.
A test fixture that extends a generic public type carries the type argument with `@extends` (for
example `@extends Collection<Invoice>` on an `Invoices` fixture), and a generics-only `@var` may
pin a type parameter at an inference point where an imprecise result feeds a typed sink (for
example `/** @var Collection<Shipment> $shipments */` before passing a mapped collection to
`Shipments::createFrom(...)`). These tags carry only the type-parameter information, never a
summary or prose description. Every other form of PHPDoc (summaries, `@param`/`@return`
descriptions on test methods, fixtures, data providers, or anonymous classes) stays prohibited.
This is the same carve-out stated in `php-library-code-style.md` under "When prohibited",
restated here because it most often surfaces on collection fixtures and inference points in
`tests/`.

## Structure: Given/When/Then (BDD)

Every test uses `/** @Given */`, `/** @And */`, `/** @When */`, `/** @Then */` doc comments
without exception.

### Happy path example

```php
public function testAddMoneyWhenSameCurrencyThenAmountsAreSummed(): void
{
    /** @Given two money instances in the same currency */
    $ten = Money::of(amount: 1000, currency: Currency::BRL);

    /** @And another money instance with the same currency */
    $five = Money::of(amount: 500, currency: Currency::BRL);

    /** @When adding them together */
    $total = $ten->add(other: $five);

    /** @Then the result contains the sum of both amounts */
    self::assertEquals(1500, $total->amount());
}
```

### Exception example

When testing that an exception is thrown, place `@Then` (`expectException`) before `@When`.
PHPUnit requires this ordering.

```php
public function testAddMoneyWhenDifferentCurrenciesThenCurrencyMismatch(): void
{
    /** @Given two money instances in different currencies */
    $brl = Money::of(amount: 1000, currency: Currency::BRL);

    /** @And another money instance with a different currency */
    $usd = Money::of(amount: 500, currency: Currency::USD);

    /** @Then an exception indicating currency mismatch should be thrown */
    $this->expectException(CurrencyMismatch::class);

    /** @When trying to add money with different currencies */
    $brl->add(other: $usd);
}
```

## Testing exceptions

Exception classes are value objects describing an invariant violation. They are not the subject
of behavior tests. A test verifies that a public method, under specific conditions, raises a
specific exception. Constructing the exception directly and asserting on its accessors is
prohibited. The exception's structure is exercised through the call path that produces it.

**Prohibited.** Testing the exception as a value object:

```php
public function testFromWhenAllFieldsGivenThenExposesEveryAccessor(): void
{
    /** @Given a URL */
    $url = 'https://api.example.com';

    /** @And an HTTP method */
    $method = Method::GET;

    /** @And a reason */
    $reason = 'Connection refused.';

    /** @When the exception is constructed */
    $exception = HttpNetworkFailed::from(url: $url, method: $method, reason: $reason);

    /** @Then it exposes the URL */
    self::assertSame($url, $exception->url());
}
```

The test constructs the exception in isolation and asserts on its accessors. No production code
is exercised. The same coverage is achieved (and made meaningful) by the test below, which
drives the path that raises the exception.

**Correct.** Testing the behavior that raises the exception:

```php
public function testSendRequestWhenTransportCannotReachServerThenThrowsHttpNetworkFailed(): void
{
    /** @Given an HTTP client backed by a transport that always raises a network error */
    $http = Http::usingTransport(transport: new ThrowingClient());

    /** @And a target request to that transport */
    $request = Request::create(url: 'https://api.example.com', method: Method::GET);

    /** @Then a network failure exception describing the unreachable target is raised */
    $this->expectException(HttpNetworkFailed::class);

    /** @When the request is sent */
    $http->send(request: $request);
}
```

When the accessor values on the raised exception are part of the assertion, `expectException`
alone is not enough (it asserts only the class). Use a `try`/`catch` block as permitted by
rule 14. The catch block contains only assertions against the caught exception, no branching.

```php
public function testSendRequestWhenTargetUnreachableThenExceptionCarriesUrlAndMethod(): void
{
    /** @Given an HTTP client backed by a transport that always raises a network error */
    $http = Http::usingTransport(transport: new ThrowingClient());

    /** @And a target request to that transport */
    $request = Request::create(url: 'https://api.example.com', method: Method::GET);

    try {
        /** @When the request is sent */
        $http->send(request: $request);
    } catch (HttpNetworkFailed $failure) {
        /** @Then the exception exposes the target URL and method */
        self::assertSame('https://api.example.com', $failure->url());
        self::assertSame(Method::GET, $failure->method());
    }
}
```

If a method does not exist whose call path produces the exception, the exception itself is dead
code. Remove it instead of writing a behavior test against a constructor.

**The `try`/`catch` form is reserved for assertions that PHPUnit's `expectException*` family
does not cover.** Message, code, and class are covered by PHPUnit (`expectException`,
`expectExceptionMessage`, `expectExceptionMessageMatches`, `expectExceptionCode`): use those
methods, not `try`/`catch`. The only case that warrants `try`/`catch` is inspecting accessors
that PHPUnit cannot reach, notably `getPrevious()` for chain inspection, or domain-specific
accessors on a `HttpNetworkFailed` (`url()`, `method()`, `reason()`).

**Prohibited.** `try`/`catch` to assert message:

```php
try {
    $http->send(request: $request);
    self::fail('NoMoreResponses was expected.');
} catch (NoMoreResponses $exception) {
    self::assertStringContainsString('queue exhausted', $exception->getMessage());
}
```

**Correct.** PHPUnit's `expectExceptionMessage`:

```php
$this->expectException(NoMoreResponses::class);
$this->expectExceptionMessage('queue exhausted');

$http->send(request: $request);
```

## Test setup and fixtures

Checklist items 3, 4, 5, 10, and 11 govern setup blocks: one declaration per annotation, no
single-use intermediate variables, no private or helper methods, domain-named variables, and
domain-language annotations. The examples below illustrate the rules most often violated in
practice. Double naming (the `$spy`/`$mock` banlist and the class-name suffix nuance) is detailed
in "Test doubles" below.

**Prohibited.** Multiple declarations under a single annotation:

```php
/** @And two money instances in different currencies */
$usd = Money::of(amount: 500, currency: Currency::USD);
$eur = Money::of(amount: 300, currency: Currency::EUR);
```

**Correct.** One annotation per declaration:

```php
/** @And a money instance in USD */
$usd = Money::of(amount: 500, currency: Currency::USD);

/** @And a money instance in EUR */
$eur = Money::of(amount: 300, currency: Currency::EUR);
```

**Also prohibited.** Setup multi-statement grouped under a single annotation because "the
statements build one coherent concept":

```php
/** @Given transport seeded with two responses */
$first = Response::with(code: Code::OK);
$second = Response::with(code: Code::CREATED);
$transport = InMemoryTransport::with(responses: [$first, $second]);
```

Three statements, one annotation. The fact that the three lines together build a single
setup concept is **not** a license to share one annotation. Each declaration takes its own
`@And` block. The same applies under `@When` when the test prepares the input alongside the
action: the input preparation goes back to `@And` under `@Given`, and `@When` contains only
the action under test.

**Correct.** Each statement keeps its own annotation:

```php
/** @Given a first queued response */
$first = Response::with(code: Code::OK);

/** @And a second queued response */
$second = Response::with(code: Code::CREATED);

/** @And transport with both responses */
$transport = InMemoryTransport::with(responses: [$first, $second]);
```

## Test doubles

Conventions for naming and locating test doubles (mocks, spies, stubs, fakes, dummies).

### Naming

- Variables and properties never carry the technical role in their name. Never `$spy`, `$mock`,
  `$stub`, `$fake`, `$dummy`. Use the domain concept the object represents (`$gateway`,
  `$clock`, `$repository`, `$client`).
- Class names may carry the technical role as suffix when the class IS a test double
  (`ClientMock`, `GatewaySpy`, `ClockFake`). The suffix signals that the file is a collaborator
  built for tests, not a production type.

### Location

- Test doubles live at the root of `tests/Unit/`. When integration tests exist, doubles used
  there live at the root of `tests/Integration/`.
- No dedicated `Mocks/` or `Doubles/` subdirectory exists.
- Domain fixtures that represent real domain concepts live in `tests/Models/`. See
  `php-library-architecture.md` for the canonical `tests/` folder layout.

## Coverage and mutation discipline

- Never use `@codeCoverageIgnore`, attributes, or configuration that exclude code from coverage.
- Never suppress mutants via `infection.json.dist` or any other mechanism.
- If a line or mutation cannot be covered or killed, the design is wrong. Refactor the
  production code to make it testable. Never work around the tool.
- The sole exception is an irreducible internal element (a non-functional memoization
  cache, or the private constructor of a static-only surface) that cannot be reached
  publicly without harming the design. It is covered or killed through a reflection-based
  white-box test, never through suppression. See "White-box coverage of irreducible
  internals".

Canonical thresholds (MSI 100, covered MSI 100) live in `php-library-tooling.md`. They are
enforced by `infection.json.dist`. Achieving MSI 100 implies effective full coverage of `src/`
because every mutation must be killed by an assertion. This file covers only the behavioral
rules that complement those thresholds.

## White-box coverage of irreducible internals

Rules 6 and 15 are near-absolute: tests exercise the public API, refactoring is the response
when a line or mutation resists coverage, and code is never hidden from coverage or mutation.
They yield in one narrow case: an *irreducible* internal element that cannot be reached
through the public API without either removing a legitimate non-functional optimization or
defeating a deliberate design. Two such elements recur:

- **Memoization caches.** A purely non-functional cache (a resolved-mapping cache, a
  shared-instance cache, a reflection-descriptor cache) whose removal leaves behavior
  identical. The mutant that drops the cache is an equivalent mutant: no public observation
  distinguishes the cached path from the recomputed one, so no public-API test can kill it.
- **Intentionally-uncallable members.** The private constructor of a static-only surface (a
  class that exists solely to expose static factories and must never be instantiated). It is
  never executed through any public path, so its line stays uncovered by construction.

For these, and only these, a white-box test is permitted as a last resort: reflecting into
`Internal/` private state to assert that memoization holds, or reflection-invoking an
uncallable constructor so its line is covered. Such a test still follows the BDD structure
and `testXxxWhenYyyThenZzz` naming, and the repeated-invocation `@When` exception (checklist
item 3) already covers the memoization case.

This exception covers code. It never hides it. `@codeCoverageIgnore`, coverage-excluding
configuration, and mutant suppression remain prohibited without exception. The irreducible
element is killed or covered honestly through reflection, not excluded from the metric. The
burden is on demonstrating irreducibility: if the line or mutation can be reached through the
public API, or if a proportionate refactor would expose it without harming the design, this
exception does not apply and the public-API test is required. White-box access is never a
convenience and never the first resort.
