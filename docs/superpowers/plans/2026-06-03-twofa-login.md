# Two-Factor Login Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add fnOS login-time two-factor authentication support while preserving the current username/password login behavior.

**Architecture:** Keep the feature inside `FnosClient` because login encryption, response routing, and secret decryption already live there. Add small helper methods for login result classification, challenge normalization, encrypted auth payload construction, and final credential storage. Expose one new public method, `submit_twofa_code()`, for the already-bound 2FA challenge path.

**Tech Stack:** Python 3.11, asyncio, websockets, PyCryptodome AES/RSA, unittest/pytest, existing `uv run pytest` workflow.

---

## Scope

This plan implements the already-bound 2FA login flow:

```text
login(username, password)
  -> returns {"twofaRequired": True, ...}
submit_twofa_code("583213")
  -> returns final token/secret login response
```

This plan also detects the enforced-but-unbound setup state and returns `twofaSetupRequired=True`. It does not implement the TOTP binding flow because that flow uses separate frontend requests (`appcgi.tfa.security.v1.login.totpVerify`, email binding requests, and then `user.2fa.loginVerify`).

## File Structure

- Modify `fnos/client.py`
  - Owns login encryption, WebSocket message routing, login state, 2FA pending state, final credential handling, and the new public `submit_twofa_code()` API.
- Modify `test_fnos_client.py`
  - Existing offline unit test file for `FnosClient`; add 2FA helper, routing, and payload tests here.
- Modify `README.md`
  - Document the new two-step login usage and add `submit_twofa_code` to the reference table.

Do not create a separate 2FA module. The feature depends on private login encryption state (`aes_key`, `iv`, `session_id`, `login_future`) and should stay close to that state.

## Baseline Notes

`uv run pytest` requires an fnOS-compatible mock server at `127.0.0.1:5666` for integration tests. In CI, `.github/workflows/integration-tests.yml` clones `https://github.com/Timandes/fnos-mock-server.git` and starts that server before running pyfnos tests. pyfnos should not start or vendor the mock server itself.

Use these verification commands during this implementation:

```bash
uv run pytest test_fnos_client.py -v
```

Expected after each task: all tests in `test_fnos_client.py` pass.

---

### Task 1: Add Login State Classification Tests

**Files:**
- Modify: `test_fnos_client.py`
- Modify: `fnos/client.py`

- [ ] **Step 1: Write failing tests for login response classification**

Add these test methods inside `class TestFnosClient(unittest.TestCase):` in `test_fnos_client.py`, after `test_decrypt_login_secret()` and before `test_gethostname_response_routes_to_correct_future()`:

```python
    def test_final_login_success_accepts_token_and_secret_without_long_token(self):
        """最终登录成功不应依赖longToken字段"""
        client = FnosClient()

        response = {
            "uid": 1001,
            "admin": True,
            "secret": "encrypted-secret",
            "token": "short-token",
            "result": "succ",
            "reqid": "6a1ee1ca00000000000000000004",
        }

        self.assertTrue(client._is_final_login_success(response))

    def test_twofa_challenge_detection_for_bound_untrusted_device(self):
        """已绑定2FA且当前设备不可信时应该识别为验证码挑战"""
        client = FnosClient()

        response = {
            "isTwofaEnforced": True,
            "isBindTwofaSecret": True,
            "isBindSecureEmail": True,
            "secureEmail": "tim*****@gmail.com",
            "isTrustedDevice": False,
            "accessToken": "tNSYygumSut0IDJCypvre5YQsOJeYQir",
            "result": "succ",
            "reqid": "6a1ee1b700000000000000000003",
        }

        self.assertTrue(client._is_twofa_challenge(response))
        self.assertFalse(client._is_twofa_setup_challenge(response))

    def test_twofa_setup_detection_for_enforced_unbound_account(self):
        """强制2FA但未绑定TOTP时应该识别为setup挑战"""
        client = FnosClient()

        response = {
            "isTwofaEnforced": True,
            "isBindTwofaSecret": False,
            "isBindSecureEmail": False,
            "isTrustedDevice": False,
            "accessToken": "setup-access-token",
            "twofaSecret": "secret-for-qr",
            "otpauth": "otpauth://totp/fnOS",
            "result": "succ",
            "reqid": "setup-reqid",
        }

        self.assertFalse(client._is_twofa_challenge(response))
        self.assertTrue(client._is_twofa_setup_challenge(response))

    def test_handle_final_login_success_stores_optional_long_token(self):
        """最终登录响应应保存token并允许longToken缺失"""
        client = FnosClient()
        client._decrypt_login_secret = lambda encrypted_secret: "decrypted-secret"

        response = {
            "uid": 1001,
            "secret": "encrypted-secret",
            "token": "short-token",
            "result": "succ",
            "reqid": "final-reqid",
        }

        result = client._handle_final_login_success(response)

        self.assertEqual(result, response)
        self.assertEqual(client.decrypted_secret, "decrypted-secret")
        self.assertEqual(client.token, "short-token")
        self.assertIsNone(client.long_token)
        self.assertIsNone(client.twofa_pending)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest test_fnos_client.py -v
```

Expected: FAIL with `AttributeError` for missing `_is_final_login_success`, `_is_twofa_challenge`, `_is_twofa_setup_challenge`, or `_handle_final_login_success`.

- [ ] **Step 3: Add 2FA state attributes and helper methods**

In `fnos/client.py`, add these attributes in `FnosClient.__init__()` immediately after `self.login_reqid = None`:

```python
        self.twofa_pending = None
        self.twofa_future = None
        self.twofa_reqid = None
```

Add these helper methods after `_decrypt_login_secret()`:

```python
    def _is_final_login_success(self, data):
        """判断响应是否包含完整登录凭据"""
        return (
            data.get("result") == "succ"
            and "token" in data
            and "secret" in data
        )

    def _is_twofa_challenge(self, data):
        """判断响应是否为已绑定2FA的登录验证码挑战"""
        return (
            data.get("result") == "succ"
            and data.get("isBindTwofaSecret") is True
            and data.get("isTrustedDevice") is False
            and bool(data.get("accessToken"))
            and "token" not in data
            and "secret" not in data
        )

    def _is_twofa_setup_challenge(self, data):
        """判断响应是否为强制2FA但尚未绑定TOTP的挑战"""
        return (
            data.get("result") == "succ"
            and data.get("isTwofaEnforced") is True
            and data.get("isBindTwofaSecret") is False
            and bool(data.get("accessToken"))
            and "token" not in data
            and "secret" not in data
        )

    def _clear_twofa_state(self):
        """清理两步验证临时状态"""
        self.twofa_pending = None
        self.twofa_reqid = None
        self.twofa_future = None

    def _handle_final_login_success(self, data):
        """保存最终登录响应中的凭据"""
        self.login_response = data
        self.decrypted_secret = self._decrypt_login_secret(data["secret"])
        self.token = data.get("token")
        self.long_token = data.get("longToken")
        self._clear_twofa_state()
        logger.info("登录成功")
        return data
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
uv run pytest test_fnos_client.py -v
```

Expected: PASS for all tests in `test_fnos_client.py`.

- [ ] **Step 5: Commit**

```bash
git add fnos/client.py test_fnos_client.py
git commit -m "test: cover two-factor login classification"
```

---

### Task 2: Refactor Login Encryption and Preserve Backward Compatibility

**Files:**
- Modify: `test_fnos_client.py`
- Modify: `fnos/client.py`

- [ ] **Step 1: Write failing tests for login payload parameters and encryption delegation**

Add these test methods inside `class TestFnosClient(unittest.TestCase):` after the Task 1 tests:

```python
    def test_encrypt_login_data_uses_configurable_device_context(self):
        """login payload应接受stay/deviceType/deviceName参数并委托通用加密方法"""
        client = FnosClient()
        client.session_id = "session-123"
        client._generate_reqid = lambda: "login-reqid"
        client._generate_did = lambda: "device-id"
        captured_payload = {}

        def fake_encrypt_auth_data(payload):
            captured_payload.update(payload)
            return {"req": "encrypted", "payload": payload}

        client._encrypt_auth_data = fake_encrypt_auth_data

        encrypted = client._encrypt_login_data(
            "alice",
            "password",
            stay=False,
            device_type="CLI",
            device_name="pytest-device",
        )

        self.assertEqual(encrypted["req"], "encrypted")
        self.assertEqual(client.login_reqid, "login-reqid")
        self.assertEqual(captured_payload["req"], "user.login")
        self.assertEqual(captured_payload["reqid"], "login-reqid")
        self.assertEqual(captured_payload["user"], "alice")
        self.assertEqual(captured_payload["password"], "password")
        self.assertFalse(captured_payload["stay"])
        self.assertEqual(captured_payload["deviceType"], "CLI")
        self.assertEqual(captured_payload["deviceName"], "pytest-device")
        self.assertEqual(captured_payload["did"], "device-id")
        self.assertEqual(captured_payload["si"], "session-123")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest test_fnos_client.py::TestFnosClient::test_encrypt_login_data_uses_configurable_device_context -v
```

Expected: FAIL with `TypeError` because `_encrypt_login_data()` does not accept `stay`, `device_type`, and `device_name`.

- [ ] **Step 3: Add `_encrypt_auth_data()` and update `_encrypt_login_data()`**

In `fnos/client.py`, replace the existing `_encrypt_login_data()` method with these two methods:

```python
    def _encrypt_auth_data(self, payload):
        """加密登录阶段数据"""
        self.aes_key = get_random_bytes(32)

        rsa_key = RSA.import_key(self.public_key)
        rsa_cipher = PKCS1_v1_5.new(rsa_key)
        encrypted_aes_key = rsa_cipher.encrypt(self.aes_key)

        json_data = json.dumps(payload, separators=(',', ':'))
        padded_data = pad(json_data.encode('utf-8'), AES.block_size)

        self.iv = get_random_bytes(16)
        aes_cipher = AES.new(self.aes_key, AES.MODE_CBC, self.iv)
        encrypted_data = aes_cipher.encrypt(padded_data)

        return {
            "req": "encrypted",
            "iv": base64.b64encode(self.iv).decode('utf-8'),
            "rsa": base64.b64encode(encrypted_aes_key).decode('utf-8'),
            "aes": base64.b64encode(encrypted_data).decode('utf-8')
        }

    def _encrypt_login_data(
        self,
        username,
        password,
        stay=True,
        device_type="Browser",
        device_name="Mac OS-Safari",
    ):
        """加密登录数据"""
        login_data = {
            "reqid": self._generate_reqid(),
            "user": username,
            "password": password,
            "stay": stay,
            "deviceType": device_type,
            "deviceName": device_name,
            "did": self._generate_did(),
            "req": "user.login",
            "si": self.session_id
        }

        self.login_reqid = login_data["reqid"]
        return self._encrypt_auth_data(login_data)
```

Update the `login()` signature and `_encrypt_login_data()` call in `fnos/client.py`:

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

Replace:

```python
        encrypted_data = self._encrypt_login_data(username, password)
```

With:

```python
        encrypted_data = self._encrypt_login_data(
            username,
            password,
            stay=stay,
            device_type=device_type,
            device_name=device_name,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
uv run pytest test_fnos_client.py -v
```

Expected: PASS for all tests in `test_fnos_client.py`.

- [ ] **Step 5: Commit**

```bash
git add fnos/client.py test_fnos_client.py
git commit -m "refactor: share encrypted auth payload construction"
```

---

### Task 3: Route Login Challenge Responses Through Futures

**Files:**
- Modify: `test_fnos_client.py`
- Modify: `fnos/client.py`

- [ ] **Step 1: Write failing async tests for login response routing**

Add these test methods inside `class TestFnosClient(unittest.TestCase):` after the Task 2 test:

```python
    def test_process_message_routes_twofa_challenge_to_login_future(self):
        """2FA challenge响应应完成login_future并保存pending上下文"""
        import asyncio
        import json

        async def run_test():
            client = FnosClient()
            future = asyncio.Future()
            client.login_future = future
            client.login_reqid = "login-reqid"

            response = {
                "isTwofaEnforced": True,
                "isBindTwofaSecret": True,
                "isBindSecureEmail": True,
                "secureEmail": "tim*****@gmail.com",
                "isTrustedDevice": False,
                "accessToken": "access-token",
                "result": "succ",
                "reqid": "login-reqid",
            }

            await client._process_message(json.dumps(response))

            self.assertTrue(future.done())
            result = future.result()
            self.assertTrue(result["twofaRequired"])
            self.assertFalse(result["twofaSetupRequired"])
            self.assertEqual(client.twofa_pending["accessToken"], "access-token")

        asyncio.run(run_test())

    def test_process_message_routes_twofa_setup_challenge_to_login_future(self):
        """强制但未绑定2FA响应应完成login_future并标记setup required"""
        import asyncio
        import json

        async def run_test():
            client = FnosClient()
            future = asyncio.Future()
            client.login_future = future
            client.login_reqid = "setup-reqid"

            response = {
                "isTwofaEnforced": True,
                "isBindTwofaSecret": False,
                "isBindSecureEmail": False,
                "isTrustedDevice": False,
                "accessToken": "setup-access-token",
                "twofaSecret": "secret-for-qr",
                "otpauth": "otpauth://totp/fnOS",
                "result": "succ",
                "reqid": "setup-reqid",
            }

            await client._process_message(json.dumps(response))

            self.assertTrue(future.done())
            result = future.result()
            self.assertFalse(result["twofaRequired"])
            self.assertTrue(result["twofaSetupRequired"])
            self.assertEqual(client.twofa_pending["accessToken"], "setup-access-token")

        asyncio.run(run_test())

    def test_process_message_accepts_final_login_without_long_token(self):
        """最终登录响应没有longToken时也应完成login_future"""
        import asyncio
        import json

        async def run_test():
            client = FnosClient()
            client._decrypt_login_secret = lambda encrypted_secret: "decrypted-secret"
            future = asyncio.Future()
            client.login_future = future

            response = {
                "uid": 1001,
                "secret": "encrypted-secret",
                "token": "short-token",
                "result": "succ",
                "reqid": "final-reqid",
            }

            await client._process_message(json.dumps(response))

            self.assertTrue(future.done())
            self.assertEqual(future.result(), response)
            self.assertEqual(client.decrypted_secret, "decrypted-secret")
            self.assertEqual(client.token, "short-token")
            self.assertIsNone(client.long_token)

        asyncio.run(run_test())
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest test_fnos_client.py::TestFnosClient::test_process_message_routes_twofa_challenge_to_login_future test_fnos_client.py::TestFnosClient::test_process_message_routes_twofa_setup_challenge_to_login_future test_fnos_client.py::TestFnosClient::test_process_message_accepts_final_login_without_long_token -v
```

Expected: FAIL because `_process_message()` currently does not route 2FA challenges and still requires `longToken` for final login success.

- [ ] **Step 3: Add challenge handlers**

Add these methods in `fnos/client.py` after `_handle_final_login_success()`:

```python
    def _handle_twofa_challenge(self, data, context):
        """保存已绑定2FA登录挑战上下文"""
        self.twofa_pending = {
            "accessToken": data["accessToken"],
            "username": context.get("username"),
            "stay": context.get("stay", True),
            "deviceType": context.get("deviceType", "Browser"),
            "deviceName": context.get("deviceName", "Mac OS-Safari"),
        }
        self.login_response = {
            **data,
            "twofaRequired": True,
            "twofaSetupRequired": False,
        }
        return self.login_response

    def _handle_twofa_setup_challenge(self, data, context):
        """保存强制2FA绑定挑战上下文"""
        self.twofa_pending = {
            "accessToken": data["accessToken"],
            "username": context.get("username"),
            "stay": context.get("stay", True),
            "deviceType": context.get("deviceType", "Browser"),
            "deviceName": context.get("deviceName", "Mac OS-Safari"),
        }
        self.login_response = {
            **data,
            "twofaRequired": False,
            "twofaSetupRequired": True,
        }
        return self.login_response
```

- [ ] **Step 4: Store login context before sending login**

Add this attribute in `FnosClient.__init__()` after `self.twofa_reqid = None`:

```python
        self.login_context = {}
```

In `login()`, immediately before building `encrypted_data`, add:

```python
        self.login_context = {
            "username": username,
            "stay": stay,
            "deviceType": device_type,
            "deviceName": device_name,
        }
```

- [ ] **Step 5: Update `_process_message()` login branches**

In `fnos/client.py`, replace the current branch:

```python
            elif "longToken" in data and "result" in data and data["result"] == "succ":
                # 这是账号密码登录响应
                self.login_response = data
                # 解密secret字段并保存
                if "secret" in data:
                    self.decrypted_secret = self._decrypt_login_secret(data["secret"])
                    self.token = data["token"]
                    self.long_token = data["longToken"]
                    logger.debug(f"服务器返回的secret: {self.decrypted_secret}")
                if self.login_future and not self.login_future.done():
                    self.login_future.set_result(self.login_response)
                logger.info("登录成功")
```

With:

```python
            elif self._is_final_login_success(data):
                self._handle_final_login_success(data)
                logger.debug(f"服务器返回的secret: {self.decrypted_secret}")
                if self.login_future and not self.login_future.done():
                    self.login_future.set_result(self.login_response)
            elif self._is_twofa_challenge(data):
                self._handle_twofa_challenge(data, self.login_context)
                if self.login_future and not self.login_future.done():
                    self.login_future.set_result(self.login_response)
            elif self._is_twofa_setup_challenge(data):
                self._handle_twofa_setup_challenge(data, self.login_context)
                if self.login_future and not self.login_future.done():
                    self.login_future.set_result(self.login_response)
```

- [ ] **Step 6: Run tests to verify they pass**

Run:

```bash
uv run pytest test_fnos_client.py -v
```

Expected: PASS for all tests in `test_fnos_client.py`.

- [ ] **Step 7: Commit**

```bash
git add fnos/client.py test_fnos_client.py
git commit -m "feat: route two-factor login challenges"
```

---

### Task 4: Implement `submit_twofa_code()`

**Files:**
- Modify: `test_fnos_client.py`
- Modify: `fnos/client.py`

- [ ] **Step 1: Write failing tests for `submit_twofa_code()` validation and payload**

Add these test methods inside `class TestFnosClient(unittest.TestCase):` after the Task 3 tests:

```python
    def test_submit_twofa_code_requires_pending_challenge(self):
        """没有pending 2FA上下文时不能提交验证码"""
        import asyncio

        async def run_test():
            client = FnosClient()
            client.connected = True
            client.public_key = "public-key"
            client.session_id = "session-id"

            with self.assertRaises(Exception) as context:
                await client.submit_twofa_code("583213")

            self.assertIn("没有待完成的两步验证登录", str(context.exception))

        asyncio.run(run_test())

    def test_submit_twofa_code_rejects_non_six_digit_code(self):
        """验证码必须是6位数字"""
        import asyncio

        async def run_test():
            client = FnosClient()
            client.connected = True
            client.public_key = "public-key"
            client.session_id = "session-id"
            client.twofa_pending = {"accessToken": "access-token"}

            with self.assertRaises(ValueError) as context:
                await client.submit_twofa_code("abc123")

            self.assertIn("两步验证码必须是6位数字", str(context.exception))

        asyncio.run(run_test())

    def test_submit_twofa_code_builds_login_verify_payload(self):
        """submit_twofa_code应发送user.2fa.loginVerify payload"""
        import asyncio

        async def run_test():
            client = FnosClient()
            client.connected = True
            client.public_key = "public-key"
            client.session_id = "session-id"
            client.twofa_pending = {
                "accessToken": "access-token",
                "username": "alice",
                "stay": False,
                "deviceType": "CLI",
                "deviceName": "pytest-device",
            }
            client._generate_reqid = lambda: "twofa-reqid"
            client._generate_did = lambda: "device-id"
            captured_payload = {}
            sent_message = {}

            def fake_encrypt_auth_data(payload):
                captured_payload.update(payload)
                return {"req": "encrypted", "payload": payload}

            async def fake_send_message(message):
                sent_message.update(message)
                client.twofa_future.set_result({
                    "result": "fail",
                    "errno": 135168,
                    "reqid": "twofa-reqid",
                })

            client._encrypt_auth_data = fake_encrypt_auth_data
            client._send_message = fake_send_message

            response = await client.submit_twofa_code("583213", trust_device=True)

            self.assertEqual(response["errno"], 135168)
            self.assertEqual(sent_message["req"], "encrypted")
            self.assertEqual(captured_payload["req"], "user.2fa.loginVerify")
            self.assertEqual(captured_payload["reqid"], "twofa-reqid")
            self.assertEqual(captured_payload["code"], "583213")
            self.assertTrue(captured_payload["isTrustedDevice"])
            self.assertEqual(captured_payload["accessToken"], "access-token")
            self.assertEqual(captured_payload["stay"], 0)
            self.assertEqual(captured_payload["deviceName"], "pytest-device")
            self.assertEqual(captured_payload["deviceType"], "CLI")
            self.assertEqual(captured_payload["did"], "device-id")
            self.assertEqual(captured_payload["si"], "session-id")
            self.assertIsNone(client.twofa_reqid)
            self.assertIsNone(client.twofa_future)

        asyncio.run(run_test())
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest test_fnos_client.py::TestFnosClient::test_submit_twofa_code_requires_pending_challenge test_fnos_client.py::TestFnosClient::test_submit_twofa_code_rejects_non_six_digit_code test_fnos_client.py::TestFnosClient::test_submit_twofa_code_builds_login_verify_payload -v
```

Expected: FAIL with `AttributeError` because `submit_twofa_code()` does not exist.

- [ ] **Step 3: Import `re`**

In `fnos/client.py`, add `import re` with the standard-library imports:

```python
import re
```

- [ ] **Step 4: Implement `submit_twofa_code()`**

Add this public method in `fnos/client.py` after `login()` and before `login_via_token()`:

```python
    async def submit_twofa_code(self, code: str, trust_device: bool = False, timeout: float = 10.0):
        """提交两步验证码完成登录"""
        if not self.connected:
            raise NotConnectedError("未连接到服务器")

        if not self.public_key or not self.session_id:
            raise Exception("未获取到公钥或会话ID")

        if not self.twofa_pending:
            raise Exception("没有待完成的两步验证登录")

        if not re.fullmatch(r"\d{6}", code):
            raise ValueError("两步验证码必须是6位数字")

        reqid = self._generate_reqid()
        payload = {
            "reqid": reqid,
            "code": code,
            "isTrustedDevice": trust_device,
            "accessToken": self.twofa_pending["accessToken"],
            "stay": int(bool(self.twofa_pending.get("stay", True))),
            "deviceName": self.twofa_pending.get("deviceName", "Mac OS-Safari"),
            "deviceType": self.twofa_pending.get("deviceType", "Browser"),
            "did": self._generate_did(),
            "req": "user.2fa.loginVerify",
            "si": self.session_id,
        }

        self.twofa_reqid = reqid
        self.twofa_future = asyncio.Future()

        encrypted_data = self._encrypt_auth_data(payload)
        logger.debug(f"Sending 2FA verification request: {encrypted_data}")
        await self._send_message(encrypted_data)

        try:
            response = await asyncio.wait_for(self.twofa_future, timeout=timeout)
            self.twofa_reqid = None
            self.twofa_future = None
            return response
        except asyncio.TimeoutError:
            self.twofa_reqid = None
            self.twofa_future = None
            raise Exception("两步验证超时")
```

- [ ] **Step 5: Route failed twofa responses by reqid**

In `_process_message()`, add this branch before the existing login-failure branch:

```python
            elif (
                "result" in data
                and data["result"] == "fail"
                and self.twofa_reqid
                and "reqid" in data
                and data["reqid"] == self.twofa_reqid
            ):
                if self.twofa_future and not self.twofa_future.done():
                    self.twofa_future.set_result(data)
                logger.error(f"两步验证失败: {data.get('msg', data.get('errmsg', '未知错误'))}")
```

Place it immediately before:

```python
            elif "result" in data and data["result"] == "fail" and self.login_reqid and "reqid" in data and data["reqid"] == self.login_reqid:
```

- [ ] **Step 6: Run tests to verify they pass**

Run:

```bash
uv run pytest test_fnos_client.py -v
```

Expected: PASS for all tests in `test_fnos_client.py`.

- [ ] **Step 7: Commit**

```bash
git add fnos/client.py test_fnos_client.py
git commit -m "feat: add two-factor code submission"
```

---

### Task 5: Verify Successful 2FA Response Routing

**Files:**
- Modify: `test_fnos_client.py`
- Modify: `fnos/client.py`

- [ ] **Step 1: Write failing test for successful 2FA response through `_process_message()`**

Add this test method inside `class TestFnosClient(unittest.TestCase):` after the Task 4 tests:

```python
    def test_process_message_routes_successful_twofa_response_to_twofa_future(self):
        """2FA成功响应应完成twofa_future并保存登录凭据"""
        import asyncio
        import json

        async def run_test():
            client = FnosClient()
            client._decrypt_login_secret = lambda encrypted_secret: "decrypted-secret"
            future = asyncio.Future()
            client.twofa_future = future
            client.twofa_reqid = "twofa-reqid"
            client.twofa_pending = {"accessToken": "access-token"}

            response = {
                "uid": 1001,
                "admin": True,
                "secret": "encrypted-secret",
                "token": "short-token",
                "backId": "6a1ee1ca000034ed",
                "machineId": "4ee55a63ae3b0fb344e2339fa22c7a0a52425508",
                "result": "succ",
                "reqid": "twofa-reqid",
            }

            await client._process_message(json.dumps(response))

            self.assertTrue(future.done())
            self.assertEqual(future.result(), response)
            self.assertEqual(client.decrypted_secret, "decrypted-secret")
            self.assertEqual(client.token, "short-token")
            self.assertIsNone(client.long_token)
            self.assertIsNone(client.twofa_pending)

        asyncio.run(run_test())
```

- [ ] **Step 2: Run test to verify it fails if Task 3 routing is incomplete**

Run:

```bash
uv run pytest test_fnos_client.py::TestFnosClient::test_process_message_routes_successful_twofa_response_to_twofa_future -v
```

Expected before any needed routing correction: FAIL if `_process_message()` clears `twofa_future` before setting the captured future. If it already passes from Task 3 implementation, proceed to Step 4.

- [ ] **Step 3: Correct final success routing if needed**

If the test fails because `_handle_final_login_success()` clears `self.twofa_future` before `_process_message()` can resolve it, change the final success branch in `_process_message()` to capture the future first:

```python
            elif self._is_final_login_success(data):
                twofa_future = self.twofa_future
                twofa_reqid = self.twofa_reqid
                self._handle_final_login_success(data)
                logger.debug(f"服务器返回的secret: {self.decrypted_secret}")
                if twofa_future and twofa_reqid and data.get("reqid") == twofa_reqid:
                    if not twofa_future.done():
                        twofa_future.set_result(data)
                elif self.login_future and not self.login_future.done():
                    self.login_future.set_result(self.login_response)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
uv run pytest test_fnos_client.py -v
```

Expected: PASS for all tests in `test_fnos_client.py`.

- [ ] **Step 5: Commit**

```bash
git add fnos/client.py test_fnos_client.py
git commit -m "test: cover successful two-factor login routing"
```

---

### Task 6: Document the 2FA Login Flow

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update the README usage example**

In `README.md`, replace this login block in the "上手" example:

```python
    # 登录
    result = await client.login(args.user, args.password)
    print("登录结果:", result)
```

With:

```python
    # 登录
    result = await client.login(args.user, args.password)
    if result.get("twofaRequired"):
        code = input("请输入 6 位两步验证码: ")
        result = await client.submit_twofa_code(code)
    elif result.get("twofaSetupRequired"):
        raise RuntimeError("该账号需要先绑定两步验证后才能继续登录")
    print("登录结果:", result)
```

- [ ] **Step 2: Add a README 2FA section**

In `README.md`, insert this section after the "上手" code block and before "## 参考":

```markdown
## 两步验证登录

如果账号已开启两步验证，`login()` 会先返回挑战信息，而不是完整登录凭据：

```python
result = await client.login(user, password)

if result.get("twofaRequired"):
    result = await client.submit_twofa_code("123456", trust_device=False)

if result.get("twofaSetupRequired"):
    raise RuntimeError("该账号需要先绑定两步验证后才能继续登录")
```

只有最终响应中包含 `token` 和 `secret` 后，SDK 才会保存登录态并允许后续 API 请求。`trust_device=True` 会请求服务器信任当前设备，后续是否免验证码由 fnOS 服务端决定。
```

- [ ] **Step 3: Update the reference table**

In `README.md`, add this row after the `login` row:

```markdown
| FnosClient | `submit_twofa_code` | 提交两步验证码完成登录 |
```

- [ ] **Step 4: Run tests to verify docs did not affect code**

Run:

```bash
uv run pytest test_fnos_client.py -v
```

Expected: PASS for all tests in `test_fnos_client.py`.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: document two-factor login flow"
```

---

### Task 7: Final Verification

**Files:**
- Verify: `fnos/client.py`
- Verify: `test_fnos_client.py`
- Verify: `README.md`

- [ ] **Step 1: Run offline unit tests**

Run:

```bash
uv run pytest test_fnos_client.py -v
```

Expected: PASS for all tests in `test_fnos_client.py`.

- [ ] **Step 2: Run full suite against externally started fnos-mock-server**

Run:

```bash
uv run pytest
```

Expected when the GitHub `fnos-mock-server` is already running at `127.0.0.1:5666`:

```text
all tests pass
```

If no mock server is running locally, integration tests may fail with `ConnectionRefusedError`. Do not add pyfnos-side mock server startup code; update `fnos-mock-server` first when the protocol contract changes.

- [ ] **Step 3: Inspect git history for forbidden trailer**

Run:

```bash
git log --format=%B -n 10 | rg "Co-Authored-By" || true
```

Expected: no output.

- [ ] **Step 4: Inspect final status**

Run:

```bash
git status --short --branch
```

Expected:

```text
## feature/twofa-login
```

No modified or untracked files should remain.

- [ ] **Step 5: Summarize implementation**

Prepare a concise summary covering:

- `login()` now returns `twofaRequired=True` for bound 2FA challenges.
- `submit_twofa_code()` submits `user.2fa.loginVerify`.
- Final success no longer depends on `longToken`.
- `twofaSetupRequired=True` is exposed for enforced-but-unbound accounts.
- Offline unit tests pass.
- Full suite result depends on externally starting the GitHub `fnos-mock-server` at `127.0.0.1:5666`.

No commit is needed in this task unless Step 1 or Step 2 exposes a real code or docs defect that gets fixed.

---

## Self-Review

**Spec coverage:**

- FR-1 final success with optional `longToken`: Task 1, Task 3, Task 5.
- FR-2 already-bound 2FA challenge: Task 1, Task 3.
- FR-3 enforced-but-unbound setup challenge: Task 1, Task 3.
- FR-4 submit code: Task 4.
- FR-5 trust-device option: Task 4.
- FR-6 post-login behavior unchanged: Task 1, Task 5, Task 7.
- README documentation: Task 6.

**Completeness scan:** This plan contains no unresolved filler text, incomplete task references, or unspecified implementation steps.

**Type consistency:** The plan consistently uses `twofa_pending`, `twofa_future`, `twofa_reqid`, `login_context`, `_encrypt_auth_data()`, `_is_final_login_success()`, `_is_twofa_challenge()`, `_is_twofa_setup_challenge()`, `_handle_final_login_success()`, `_handle_twofa_challenge()`, `_handle_twofa_setup_challenge()`, and `submit_twofa_code()`.
