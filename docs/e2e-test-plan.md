# End-to-End (Playwright) Test Plan — Plain English

This describes the E2E test suite we're adding on top of the existing unit/integration
tests in `test-plan.md`. Those tests check individual pieces (a route, a DB model, a
component) in isolation. These tests check that a real user can actually click through
the app and have everything work together — frontend, API, Postgres, and Neo4j, all at once.

## What runs it

The tests start the whole app for real: Postgres, Neo4j, the FastAPI backend, and the
built frontend, all via Docker Compose (a test-only variant of the compose file we
already have). Playwright then drives a real browser against that stack, the same way
a person would.

## Each test uses its own fake user

Every test creates its own brand-new account with a made-up, unique email address
(something like `e2e-run123-test7@example.com`). That way tests never interfere with
each other and can safely run at the same time.

## Cleaning up after ourselves

This is the part you asked us to get right: **nothing sticks around in the databases.**

- Right after each test finishes, we delete that test's user. This automatically removes
  their profile too (it's set up to cascade), and we also remove their matching node in
  Neo4j.
- As a backup, at the very end of the whole test run we do one more sweep and delete
  anything left over that matches this run's test-user pattern — in case a test crashed
  partway through and skipped its own cleanup.

Net effect: run the suite 100 times, and your database looks exactly the same
afterward as before.

## What we're actually testing

**The main journey (one test, start to finish):**
Register → log in → fill out profile → see personalized recommendations → browse/search
jobs. This is the "does the whole product work" smoke test.

**Plus, per feature, the important edge cases:**
- **Registration** — normal signup works; signing up twice with the same email is
  rejected; bad input shows a validation error.
- **Login** — correct password works; wrong password is rejected; unknown email is
  rejected.
- **Profile completion** — an incomplete profile blocks/limits recommendations;
  finishing the profile unlocks them.
- **Recommendations** — the recommendations you get actually reflect the skills you
  entered (not just "a page loaded").
- **Job Explorer** — searching/filtering works, an empty search shows a proper empty
  state, opening a job shows its details.

## Where the files will live

```
frontend/tests/e2e/
  fixtures/     -- reusable setup: creating a test user, logging in, DB cleanup
  specs/        -- the actual test files, one per feature above
```

## When it runs

Locally, on demand, and in CI on every relevant change — Compose brings the whole stack
up, Playwright runs, and everything gets torn down afterward regardless of pass/fail.
