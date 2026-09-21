# Security

- Never store Upwork passwords, session cookies, browser tokens, or credentials in source control.
- Passwords are hashed; plaintext passwords are never persisted or logged.
- Account-affecting actions require explicit, recorded user approval.
- AI output is untrusted input until validated and, where factual, checked against verified claims.
- Client facts retain source records; AI-generated inferences cannot be promoted to verified facts.
- Client analysis rejects unsupported fact IDs, and portfolio explanations reject unsupported project or claim IDs.
- Proposal-ready evidence links require database-verified skills and claims.
- Production deployments must use a strong `JWT_SECRET`, HTTPS, managed secrets, database backups, and row-level authorization controls.
- Logs and audit records must reference sensitive inputs rather than copying credentials or private message bodies unnecessarily.

Security tests cover authentication boundaries, database constraints, verification-state rules, source retention, and hallucinated evidence rejection. Phase 3 does not fetch external client information; only explicitly supplied or sample-fixture data is accepted.
