"""Deployment-independent HTTP readiness checks."""

from dataclasses import dataclass
from time import monotonic, sleep
from typing import Callable
from urllib.request import urlopen

from .errors import OkapiCtlError


@dataclass(frozen=True)
class HealthEndpoint:
    """An HTTP endpoint that must return a successful status code."""

    name: str
    url: str


class HealthChecker:
    """Wait for a set of HTTP health endpoints to become ready."""

    def __init__(
        self,
        request: Callable[[str, float], int] | None = None,
        sleep_fn: Callable[[float], None] = sleep,
        clock: Callable[[], float] = monotonic,
    ):
        self._request = request or self._request_status
        self._sleep = sleep_fn
        self._clock = clock

    def wait_for_all(
        self,
        endpoints: list[HealthEndpoint],
        *,
        timeout_seconds: int,
        failure_hint: str | None = None,
    ) -> None:
        for endpoint in endpoints:
            self.wait_for(
                endpoint,
                timeout_seconds=timeout_seconds,
                failure_hint=failure_hint,
            )

    def wait_for(
        self,
        endpoint: HealthEndpoint,
        *,
        timeout_seconds: int,
        failure_hint: str | None = None,
    ) -> None:
        deadline = self._clock() + timeout_seconds
        while self._clock() < deadline:
            try:
                status = self._request(endpoint.url, 5.0)
                if 200 <= status < 300:
                    return
            except OSError:
                pass
            self._sleep(2)

        message = f"Timed out waiting for {endpoint.name} at {endpoint.url}."
        if failure_hint:
            message += f" {failure_hint}"
        raise OkapiCtlError(message)

    @staticmethod
    def _request_status(url: str, timeout: float) -> int:
        with urlopen(url, timeout=timeout) as response:
            return response.status

