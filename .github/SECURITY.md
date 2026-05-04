# Security Policy

## Supported Scope

This repository is public. Please report:

- credential or secret exposure
- authorization bypass or privilege escalation
- injection or data exposure flaws
- CI or supply-chain risks in GitHub Actions or dependencies

## Reporting A Vulnerability

Please do not open a public GitHub issue for an active security problem.

Instead:

1. Open a GitHub private vulnerability report if that option is enabled for this repository.
2. If private reporting is unavailable, contact the repository owner directly and include:
   - a short description of the issue
   - the affected file or endpoint
   - reproduction steps
   - impact and any suggested mitigation

## Secret Handling

- Never commit private keys, service-role keys, database passwords, or local bootstrap scripts with real values.
- Treat `aws/*.pem`, `aws/demo-user-data.sh`, and local `.env` files as local-only artifacts.
- Rotate any credential immediately if you believe it may have been exposed.
