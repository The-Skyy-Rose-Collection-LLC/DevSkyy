// scripts/measurement/_lib/google-jwt.js
// Shared JWT client factory for the GA4, GSC, and GTM verifiers.
//
// All three Google verifiers consume the same GOOGLE_SERVICE_ACCOUNT_JSON env var
// and differ only in the API scope they request. Centralising here means scope
// typos and JSON-parsing bugs are fixed in one place.
//
// HTTP behaviour: callers use the returned client's `client.fetch(url, init)` directly.
// That's the API the library is designed around (see google-auth-library 10.x docs and
// Context7 /googleapis/google-auth-library-nodejs); it auto-injects the auth header and
// follows gaxios semantics — including throwing on 4xx/5xx, which the verifiers handle
// in try/catch and read err.status + err.response.data.

import { JWT } from 'google-auth-library';

export const SCOPES = {
  GA4: 'https://www.googleapis.com/auth/analytics.readonly',
  GSC: 'https://www.googleapis.com/auth/webmasters.readonly',
  GTM: 'https://www.googleapis.com/auth/tagmanager.readonly',
};

function parseServiceAccount() {
  const raw = process.env.GOOGLE_SERVICE_ACCOUNT_JSON;
  if (!raw) {
    throw Object.assign(new Error('GOOGLE_SERVICE_ACCOUNT_JSON not set'), { code: 'ENOENV' });
  }
  let keys;
  try {
    keys = JSON.parse(raw);
  } catch (err) {
    throw Object.assign(
      new Error(
        `GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON. Vercel often mangles multi-line pastes — re-add it via "vercel env add GOOGLE_SERVICE_ACCOUNT_JSON production < /path/to/key.json". Parse error: ${err.message}`
      ),
      { code: 'EBADJSON' }
    );
  }
  for (const required of ['client_email', 'private_key', 'project_id']) {
    if (!keys[required]) {
      throw Object.assign(
        new Error(`GOOGLE_SERVICE_ACCOUNT_JSON missing required field "${required}"`),
        { code: 'EBADKEY' }
      );
    }
  }
  return keys;
}

export function createJwtClient(scope) {
  const keys = parseServiceAccount();
  return new JWT({
    email: keys.client_email,
    key: keys.private_key,
    scopes: Array.isArray(scope) ? scope : [scope],
  });
}

export function getServiceAccountEmail() {
  return parseServiceAccount().client_email;
}

// Normalises gaxios errors so verifiers can branch on HTTP status uniformly.
// Network errors (no response) surface as { status: 0, data: { error: { message } } }.
export function readGaxiosError(err) {
  return {
    status: err.status ?? err.response?.status ?? 0,
    data: err.response?.data ?? { error: { message: err.message } },
  };
}
