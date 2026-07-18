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

## Verify

No dedicated test dir; exercised manually per docs/sso_via_saml_mscolab.rst.
Run `pixi run -e dev lint` and `pixi run -e dev lint-imports`.
