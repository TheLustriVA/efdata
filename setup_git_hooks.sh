#!/bin/bash
# Setup script for git hooks

echo "Setting up git hooks..."

# Configure git to use our hooks directory
git config core.hooksPath .githooks

echo "✅ Git hooks configured"
echo ""
echo "The pre-push hook will now check for:"
echo "  - Hardcoded passwords and secrets"
echo "  - Large files (>1MB)"
echo "  - Database dumps"
echo ""
echo "To test the hook: git push --dry-run"
echo "To bypass (NOT recommended): git push --no-verify"