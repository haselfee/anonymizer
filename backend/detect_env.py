#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environment detection helpers.
Note: No behavior change; pure utilities for later use.
"""

from __future__ import annotations
import os
import pathlib


def running_in_container() -> bool:
    """
    Heuristics:
    - /.dockerenv present
    - /proc/1/cgroup mentions docker/containerd/kubepods
    """
    try:
        if pathlib.Path("/.dockerenv").exists():
            return True
    except Exception:
        pass

    try:
        with open("/proc/1/cgroup", "r", encoding="utf-8") as f:
            c = f.read().lower()
        return ("docker" in c) or ("containerd" in c) or ("kubepods" in c)
    except Exception:
        return False


def running_under_uvicorn() -> bool:
    """
    FastAPI under uvicorn typically sets SERVER_SOFTWARE=uvicorn.
    """
    return "uvicorn" in os.getenv("SERVER_SOFTWARE", "").lower()
