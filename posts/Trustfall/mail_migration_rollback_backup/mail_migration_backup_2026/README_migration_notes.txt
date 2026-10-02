TrustFall Mail Migration Notes – January 2026

- Migrated mailboxes from old Dovecot auth file to SQL backend.
- Old auth file kept temporarily for rollback.
- Ensure backup is removed after 30 days.

Temporary credentials used during testing:
example@trustfall.htb
Password pattern: CompanyName + DEPARTMENT + FirstName + BirthYear + !

Example: TrustFallITMostafa1997! / TrustFallSALESGabriel979!

-- IT Department
