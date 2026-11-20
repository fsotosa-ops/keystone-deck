# Security policy

## Supported versions

The latest minor release receives fixes.

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub's **Report a vulnerability** (Security tab → Advisories). Do not open a public issue. You can expect an acknowledgement within five working days.

## Scope and design

- The plugins run local scripts. The core makes no network calls.
- Engines may load fonts from Google Fonts and, when you opt in, call third-party APIs (for example a text-to-speech provider). Keys are read from environment variables and are never written to disk or logs.
- `brand-kit` reads a website's styles only when you name the site.
