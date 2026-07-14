import fnos


def test_https_required_error_is_public_and_structured():
    error_type = getattr(fnos, "HTTPSRequiredError", None)

    assert error_type is not None
    assert "HTTPSRequiredError" in fnos.__all__

    error = error_type(
        requested_uri="ws://nas.example.com:5666/websocket?type=main",
        redirect_uri="https://nas.example.com:5667/websocket?type=main",
        status_code=302,
    )

    assert isinstance(error, ConnectionError)
    assert error.requested_uri == "ws://nas.example.com:5666/websocket?type=main"
    assert error.redirect_uri == "https://nas.example.com:5667/websocket?type=main"
    assert error.status_code == 302
    assert "fnOS 服务端要求安全连接" in str(error)
    assert "wss://" in str(error)
    assert "use_ssl=True" in str(error)
    assert error.redirect_uri in str(error)
