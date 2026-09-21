# Security

- Never store Upwork passwords, session cookies, browser tokens, or credentials in source control.
- Passwords are hashed; plaintext passwords are never persisted or logged.
- Account-affecting actions require explicit, recorded user approval.
- AI output is untrusted input until validated and, where factual, checked against verified claims.
- Production deployments must use a strong `JWT_SECRET`, HTTPS, managed secrets, database backups, and row-level authorization controls.
- Logs and audit records must reference sensitive inputs rather than copying credentials or private message bodies unnecessarily.

Security testing expands with each feature phase. The initial phase tests authentication boundaries and database constraints.
