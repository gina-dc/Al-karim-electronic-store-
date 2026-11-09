from app.bootstrap import prompt_owner_details


def test_short_password_and_mismatch_retry_without_exposing_password(
    monkeypatch, capsys
):
    answers = iter(["owner", "Owner"])
    passwords = iter(
        [
            "short-value",
            "test-valid-password-one",
            "different-confirmation",
            "test-valid-password-two",
            "test-valid-password-two",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr("app.bootstrap.getpass.getpass", lambda _: next(passwords))
    payload = prompt_owner_details()
    output = capsys.readouterr().out
    assert payload.password == "test-valid-password-two"
    assert "12 and 128" in output
    assert "Passwords do not match" in output
    for secret in [
        "short-value",
        "test-valid-password-one",
        "different-confirmation",
        "test-valid-password-two",
    ]:
        assert secret not in output
