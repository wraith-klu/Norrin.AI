#!/usr/bin/env sh
find . -type d -name __pycache__ -prune -exec rm -rf {} +
