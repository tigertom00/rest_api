#!/bin/bash
# Comprehensive linting script for the Django project

set -e

echo "🔍 Running Python linting tools..."

# Activate virtual environment
source .venv/bin/activate

echo "📋 Running ruff (linting + import sorting)..."
ruff check --fix .

echo "🎨 Running black (code formatting)..."
black .

echo "📦 Running isort (import sorting)..."
isort .

echo "🔍 Running flake8 (additional linting)..."
flake8

echo "🏷️  Running mypy (type checking)..."
mypy --install-types --non-interactive --ignore-missing-imports .

echo "✅ All linting tools completed successfully!"
