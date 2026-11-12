# mslib.msidp — SAML2 identity provider

Purpose: standalone identity provider (`msidp` entry point) for testing the
MSColab single-sign-on flow (see docs/sso_via_saml_mscolab.rst). Not imported
by any other mslib package.
Global map: ../../ARCHITECTURE.md

## Layout

- `idp.py` — pysaml2-based IdP service (entry: `main`)
- `idp_conf.py` — certificates/endpoints config; `idp_user.py` — test users

## Invariants

- Keep isolated: nothing in mslib may import msidp, and msidp must not import
  other mslib packages.
- Changes here usually pair with `mslib/mscolab/blueprints/auth` (SAML routes)
  and docs/sso_via_saml_mscolab.rst.
- msidp is test-only and says so on start; it still must not log passwords or
  session ids, take a session id from the URL, or render request data unescaped.

## Verify

`tests/_test_msidp` (sessions, cookies, logs, error messages; WSGI app with a
stand-in pysaml2 server). The full SSO flow with MSColab is exercised manually
per docs/conf_sso_test_msscolab.rst; MSColab's side of it is covered by
`tests/_test_mscolab/test_saml.py` with an in-process pysaml2 IdP (needs
`xmlsec1`, skipped without it). Run `pixi run -e dev lint` and
`pixi run -e dev lint-imports`.
With only its dependencies (no numpy, no Flask): `pixi run -e msidp test-msidp`.
