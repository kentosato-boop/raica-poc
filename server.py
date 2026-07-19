#!/usr/bin/env python3
"""Compatibility launcher for local development."""

import uvicorn


if __name__ == "__main__":
    uvicorn.run("app.main:app", app_dir="backend", host="127.0.0.1", port=8000, reload=False)
