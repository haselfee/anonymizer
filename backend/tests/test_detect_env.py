# backend/tests/test_detect_env.py
from __future__ import annotations

import builtins
import importlib
import io

import pytest

# Dank pytest.ini (pythonpath = backend) können wir top-level importieren:
import detect_env  # type: ignore


def test_running_in_container_by_dockerenv(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = importlib.reload(detect_env)

    # /.dockerenv existiert → True
    original_exists = mod.pathlib.Path.exists

    def fake_exists(self: mod.pathlib.Path) -> bool:
        if str(self) == "/.dockerenv":
            return True
        return original_exists(self)

    monkeypatch.setattr(mod.pathlib.Path, "exists", fake_exists, raising=True)
    assert mod.running_in_container() is True


def test_running_in_container_by_cgroup(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = importlib.reload(detect_env)

    # /.dockerenv existiert NICHT
    def fake_exists(self: mod.pathlib.Path) -> bool:
        return False

    monkeypatch.setattr(mod.pathlib.Path, "exists", fake_exists, raising=True)

    # /proc/1/cgroup enthält "docker" → True
    original_open = builtins.open

    def fake_open(file, mode="r", encoding=None):
        if file == "/proc/1/cgroup":
            return io.StringIO("0::/docker/abcd\n")
        return original_open(file, mode)

    # WICHTIG: sowohl builtins.open patchen als auch mod.open injizieren
    monkeypatch.setattr(builtins, "open", fake_open, raising=True)
    monkeypatch.setattr(mod, "open", fake_open, raising=False)

    assert mod.running_in_container() is True


def test_running_in_container_negative(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = importlib.reload(detect_env)

    # Weder /.dockerenv noch docker/containerd/kubepods im cgroup
    def fake_exists(self: mod.pathlib.Path) -> bool:
        return False

    monkeypatch.setattr(mod.pathlib.Path, "exists", fake_exists, raising=True)

    original_open = builtins.open

    def fake_open(file, mode="r", encoding=None):
        if file == "/proc/1/cgroup":
            return io.StringIO("0::/init.scope\n")
        return original_open(file, mode)

    monkeypatch.setattr(builtins, "open", fake_open, raising=True)
    monkeypatch.setattr(mod, "open", fake_open, raising=False)

    assert mod.running_in_container() is False


def test_running_under_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = importlib.reload(detect_env)

    monkeypatch.setenv("SERVER_SOFTWARE", "uvicorn")
    assert mod.running_under_uvicorn() is True

    monkeypatch.setenv("SERVER_SOFTWARE", "gunicorn")
    assert mod.running_under_uvicorn() is False
