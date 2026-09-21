# Agent development rules

1. Use `sample_jobs/` for all engine development until the authorized integration phase.
2. Do not add scraping, browser-login automation, cookies, CAPTCHA handling, or Upwork credentials.
3. Keep model IDs in environment-backed settings.
4. Use deterministic code for validation, authorization, deduplication, scoring boundaries, state transitions, and fact support checks.
5. An AI agent may propose content but may not perform account-affecting actions.
6. Proposal claims must trace to `VERIFIED` knowledge-base records or be flagged for review.
7. Keep route handlers thin and version AI prompts.
8. Add tests and update documentation in the same phase as behavior changes.
9. Do not mark a phase complete without running its tests.
