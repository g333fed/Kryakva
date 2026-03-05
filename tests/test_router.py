from app.commands.router import CommandRouter


def test_hotword_command_routes_to_explorer() -> None:
    router = CommandRouter()
    result = router.route("кряква открой проводник")
    assert result.intent == "cmd"
    assert result.command == "open_explorer"


def test_open_url_argument_normalization() -> None:
    router = CommandRouter()
    result = router.route("открой example.com")
    assert result.intent == "cmd"
    assert result.command == "open_url"
    assert result.argument == "https://example.com"
