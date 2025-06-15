#!/bin/bash

set -e

ruff format xrouter/
mypy xrouter/
