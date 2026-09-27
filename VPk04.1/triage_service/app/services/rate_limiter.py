import time
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._clients: dict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        dq = self._clients[client_id]

        while dq and dq[0] < now - self.window_seconds:
            dq.popleft()

        if len(dq) >= self.max_requests:
            return False

        dq.append(now)
        return True