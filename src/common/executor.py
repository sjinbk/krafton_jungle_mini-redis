from __future__ import annotations

from concurrent.futures import Future
from dataclasses import dataclass
from queue import Queue
from threading import Event, Lock, Thread, get_ident
from typing import Any, Callable


_STOP = object()


@dataclass(slots=True)
class _QueuedCommand:
    fn: Callable[..., Any]
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    future: Future[Any]


class SingleThreadCommandExecutor:
    def __init__(self, *, thread_name: str = "mini-redis-command-executor") -> None:
        self._queue: Queue[_QueuedCommand | object] = Queue()
        self._closed = Event()
        self._state_lock = Lock()
        self._worker = Thread(target=self._run, name=thread_name, daemon=True)
        self._worker.start()

    def run(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if self._is_worker_thread():
            return fn(*args, **kwargs)

        with self._state_lock:
            if self._closed.is_set():
                raise RuntimeError("Command executor is closed")

            future: Future[Any] = Future()
            self._queue.put(
                _QueuedCommand(
                    fn=fn,
                    args=args,
                    kwargs=kwargs,
                    future=future,
                )
            )

        return future.result()

    def shutdown(self) -> None:
        with self._state_lock:
            if self._closed.is_set():
                return

            self._closed.set()
            self._queue.put(_STOP)

        if self._worker.is_alive() and not self._is_worker_thread():
            self._worker.join(timeout=2)

    def _is_worker_thread(self) -> bool:
        return get_ident() == self._worker.ident

    def _run(self) -> None:
        while True:
            command = self._queue.get()
            if command is _STOP:
                return

            try:
                result = command.fn(*command.args, **command.kwargs)
            except Exception as exc:
                command.future.set_exception(exc)
            else:
                command.future.set_result(result)
