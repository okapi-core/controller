from okapictl.health import HealthChecker, HealthEndpoint


def test_health_checker_retries_until_endpoint_is_ready():
    responses = iter([503, 200])
    waits = []

    checker = HealthChecker(
        request=lambda _url, _timeout: next(responses),
        sleep_fn=waits.append,
    )
    checker.wait_for(
        HealthEndpoint("web", "http://web/internal/healthcheck"),
        timeout_seconds=10,
    )

    assert waits == [2]

