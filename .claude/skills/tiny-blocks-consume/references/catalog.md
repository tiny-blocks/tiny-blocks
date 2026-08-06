# tiny-blocks catalog

Index of published tiny-blocks packages and their one-line purpose. Generated from Packagist by
scripts/refresh-catalog.py, not hand-maintained. For the full API of a package, read its README
and public PHPDoc under vendor/tiny-blocks/<name>/.

- `tiny-blocks/building-blocks`: Implements tactical DDD building blocks for PHP: entities, aggregate roots, domain
  events, snapshots, and upcasters.
- `tiny-blocks/collection`: Models a type-safe, fluent collection API for PHP with eager and lazy pipelines over arrays,
  iterators, and generators.
- `tiny-blocks/country`: Provides ISO 3166-1 country and ISO 3166-2 subdivision value objects for PHP, with Alpha-2,
  Alpha-3, numeric, and IANA timezone resolution.
- `tiny-blocks/currency`: Models ISO-4217 currencies as a PHP enum, with per-currency fraction digit resolution.
- `tiny-blocks/docker-container`: Manages Docker containers programmatically for PHP, aimed at integration tests and
  disposable infrastructure.
- `tiny-blocks/encoder`: Encoder and decoder for arbitrary data.
- `tiny-blocks/environment-variable`: Provides a type-safe environment variable reader for PHP, with strict integer and
  boolean conversion.
- `tiny-blocks/http`: Implements PSR-7, PSR-15, PSR-17 and PSR-18 HTTP primitives for PHP, with a fluent response
  builder, cookies, cache control, and a PSR-18 client facade.
- `tiny-blocks/http-correlation-id`: Ensures every HTTP request has a correlation identifier propagated through
  requests, responses, and logs.
- `tiny-blocks/http-error-handler`: PSR-15 error handler that maps thrown exceptions to structured JSON error responses
  with optional logging.
- `tiny-blocks/http-health-check`: PSR-15 liveness and readiness request handlers with configurable health checks for
  HTTP services.
- `tiny-blocks/http-logging`: PSR-15 middleware that logs HTTP request and response metadata with request duration.
- `tiny-blocks/http-query`: Typed, framework-independent toolkit for HTTP collection queries (RSQL filtering, sorting,
  and offset and cursor pagination) that never touches a data store.
- `tiny-blocks/immutable-object`: Provides immutable behavior for objects.
- `tiny-blocks/ksuid`: K-Sortable Unique Identifier.
- `tiny-blocks/logger`: Emits PSR-3 structured logs for PHP, with correlation tracking and configurable sensitive data
  redaction.
- `tiny-blocks/mapper`: Maps PHP objects to and from arrays, JSON, and iterables through reflection and pluggable
  strategies.
- `tiny-blocks/math`: Value Objects for handling arbitrary precision numbers.
- `tiny-blocks/outbox`: Write-side adapter for the Transactional Outbox pattern that persists domain events atomically
  with aggregate state through Doctrine DBAL.
- `tiny-blocks/time`: Models time as immutable value objects for PHP: instants, durations, periods, timezones, and
  time-of-day, all UTC-normalized.
- `tiny-blocks/value-object`: Defines the default behavior contract for PHP value objects with structural equality.
