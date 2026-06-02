# Two-Factor Login Support Specification

## Overview

Add two-factor authentication support to `FnosClient` login while keeping the current username/password flow compatible.

fnOS may respond to `user.login` in three ways:

1. Final login success, with `token` and `secret`.
2. A 2FA challenge for an account that already has TOTP bound.
3. A 2FA setup challenge for an account where 2FA is enforced but TOTP is not bound.

The SDK must let the caller know when a second step is required, and provide a dedicated method to submit the 6-digit code for the already-bound 2FA case.

## Confirmed Frontend Behavior

The fnOS login page loads `/assets/index-BgSAan-c.js`, which imports `/assets/useTfaLogin-DktzBFEw.js`.

The frontend uses these request names:

- `user.login` for username/password login.
- `user.2fa.loginVerify` for login-time 2FA verification.
- `appcgi.tfa.security.v1.login.totpVerify` for initial TOTP binding during enforced setup.
- `appcgi.tfa.security.v1.login.sendEmailCode` for login-time secure-email code flows.

For an already-bound 2FA account, the frontend submits:

```json
{
  "req": "user.2fa.loginVerify",
  "code": "583213",
  "isTrustedDevice": false,
  "accessToken": "<challenge access token>",
  "stay": 1,
  "deviceName": "Mac OS-Safari",
  "deviceType": "Browser",
  "did": "<generated device id>"
}
```

The SDK should also include `reqid` and `si` as it does for other encrypted login-stage requests.

## Functional Requirements

### FR-1: Preserve normal login behavior

**WHEN** the server returns a final login response containing `result == "succ"`, `token`, and `secret`,
**THEN THE SYSTEM SHALL** treat the login as complete,
**AND** decrypt and store `secret`,
**AND** store `token`,
**AND** store `longToken` when present,
**AND** return the server response.

`longToken` is optional. A final 2FA verification response may contain `token` and `secret` without `longToken`.

### FR-2: Detect an already-bound 2FA challenge

**WHEN** `user.login` returns `result == "succ"`, `isBindTwofaSecret == true`, `isTrustedDevice == false`, and `accessToken`,
**AND** the response does not contain `token` and `secret`,
**THEN THE SYSTEM SHALL** return the response with:

```json
{
  "twofaRequired": true,
  "twofaSetupRequired": false
}
```

**AND** store the pending 2FA context required by `submit_twofa_code()`.

### FR-3: Detect an enforced 2FA setup challenge

**WHEN** `user.login` returns `result == "succ"`, `isTwofaEnforced == true`, `isBindTwofaSecret == false`, and `accessToken`,
**THEN THE SYSTEM SHALL** return the response with:

```json
{
  "twofaRequired": false,
  "twofaSetupRequired": true
}
```

**AND** avoid treating this as a normal code-submission challenge.

The first implementation will expose this state to callers but will not complete the full TOTP binding flow automatically.

### FR-4: Submit an already-bound 2FA code

**WHEN** the caller invokes `submit_twofa_code(code)`,
**THEN THE SYSTEM SHALL** validate that a pending 2FA challenge exists,
**AND** validate that `code` is exactly six digits,
**AND** send an encrypted `user.2fa.loginVerify` request using the pending challenge context.

### FR-5: Trust-device option

**WHEN** the caller invokes `submit_twofa_code(code, trust_device=True)`,
**THEN THE SYSTEM SHALL** send `isTrustedDevice: true`.

The default is `False`.

### FR-6: Keep post-login request behavior unchanged

**WHEN** final login succeeds through either normal login or 2FA verification,
**THEN THE SYSTEM SHALL** populate `decrypted_secret`,
**AND** allow existing `request()`, `request_payload()`, and manager APIs to operate without special 2FA handling.

## API Design

### login()

Extend the current method signature with optional device context parameters:

```python
async def login(
    self,
    username,
    password,
    timeout: float = 10.0,
    stay: bool = True,
    device_type: str = "Browser",
    device_name: str = "Mac OS-Safari",
):
```

Existing calls remain valid:

```python
result = await client.login("admin", "admin")
```

Challenge handling:

```python
result = await client.login(username, password)

if result.get("twofaRequired"):
    result = await client.submit_twofa_code(code)

if result.get("twofaSetupRequired"):
    raise RuntimeError("This account must bind 2FA before SDK login can continue")
```

### submit_twofa_code()

Add a new method:

```python
async def submit_twofa_code(
    self,
    code: str,
    trust_device: bool = False,
    timeout: float = 10.0,
):
```

This method sends:

```python
{
    "req": "user.2fa.loginVerify",
    "reqid": reqid,
    "code": code,
    "isTrustedDevice": trust_device,
    "accessToken": self.twofa_pending["accessToken"],
    "stay": int(self.twofa_pending.get("stay", True)),
    "deviceName": self.twofa_pending.get("deviceName", "Mac OS-Safari"),
    "deviceType": self.twofa_pending.get("deviceType", "Browser"),
    "did": self._generate_did(),
    "si": self.session_id,
}
```

## Internal Design

### State

Add these instance attributes:

```python
self.twofa_pending = None
self.twofa_future = None
self.twofa_reqid = None
```

`twofa_pending` stores:

```python
{
    "accessToken": "...",
    "username": "...",
    "stay": true,
    "deviceType": "Browser",
    "deviceName": "Mac OS-Safari"
}
```

### Helpers

Add focused helpers:

```python
def _encrypt_auth_data(self, payload: dict) -> dict
def _is_final_login_success(self, data: dict) -> bool
def _is_twofa_challenge(self, data: dict) -> bool
def _is_twofa_setup_challenge(self, data: dict) -> bool
def _handle_final_login_success(self, data: dict) -> dict
def _handle_twofa_challenge(self, data: dict, context: dict) -> dict
def _handle_twofa_setup_challenge(self, data: dict, context: dict) -> dict
```

`_encrypt_login_data()` should assemble the `user.login` payload and delegate encryption to `_encrypt_auth_data()`.

`submit_twofa_code()` should assemble the `user.2fa.loginVerify` payload and delegate encryption to `_encrypt_auth_data()`.

### Final Success Detection

Use credential presence instead of `longToken`:

```python
data.get("result") == "succ" and "token" in data and "secret" in data
```

This supports final 2FA responses that omit `longToken`.

### Message Routing

`_process_message()` should complete `login_future` when a login response is:

- Final login success.
- Already-bound 2FA challenge.
- Enforced 2FA setup challenge.
- Login failure matching `login_reqid`.

It should complete `twofa_future` when a response matches `twofa_reqid`, including both success and failure.

On final success through either route, clear:

```python
self.twofa_pending = None
self.twofa_reqid = None
self.twofa_future = None
```

## Error Handling

Return server failure responses from `login()` and `submit_twofa_code()` when the request completes but the server rejects it.

Raise exceptions for SDK usage or transport problems:

- Not connected.
- Missing RSA public key or session id.
- Calling `submit_twofa_code()` without a pending 2FA challenge.
- Code is not exactly six digits.
- Timeout.

Known server error semantics:

- `135168`: verification code error in the frontend.
- `102570109`: login 2FA credential expired; caller should restart `login()`.

## Testing

### Unit Tests

Add offline unit tests for:

- `_is_final_login_success()` accepts `token + secret` without `longToken`.
- `_is_twofa_challenge()` recognizes the captured already-bound challenge shape.
- `_is_twofa_setup_challenge()` recognizes enforced-but-unbound 2FA.
- `submit_twofa_code()` rejects missing pending state.
- `submit_twofa_code()` rejects non-6-digit values.
- `submit_twofa_code()` builds a `user.2fa.loginVerify` payload with `code`, `accessToken`, `isTrustedDevice`, `stay`, `deviceName`, and `deviceType`.
- Final 2FA response handling saves `token`, optional `longToken`, and decrypted secret.

Mock encryption in payload-shape tests by overriding `_encrypt_auth_data()`.

### Integration Tests

Existing integration tests require an fnOS service at `127.0.0.1:5666`. They should not be the primary verification path for this feature unless such a service is running.

Manual integration verification should cover:

- Account without 2FA.
- Account with bound 2FA and untrusted device.
- Account with bound 2FA and `trust_device=True`.
- Account where 2FA is enforced but not bound.

## Acceptance Criteria

- [ ] Existing `await client.login(username, password)` calls still work for non-2FA users.
- [ ] `login()` returns `twofaRequired=True` for already-bound 2FA challenges.
- [ ] `submit_twofa_code()` submits `user.2fa.loginVerify`.
- [ ] Final 2FA response without `longToken` is accepted.
- [ ] `get_decrypted_secret()` is populated only after final login success.
- [ ] `twofaSetupRequired=True` is returned for enforced-but-unbound accounts.
- [ ] Unit tests cover all offline login-state decisions.
- [ ] README documents the new 2FA login flow.
