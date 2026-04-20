#!/usr/bin/env bash
set -euo pipefail

# Usage: tag-release.sh [-y]
#   -y  skip confirmation prompt (for non-interactive use)
YES=false
while getopts "y" opt; do
  case $opt in
    y) YES=true ;;
    *) echo "Usage: $0 [-y]"; exit 1 ;;
  esac
done

VERSION=$(grep '^version' pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
TAG="v${VERSION}"

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Tag $TAG already exists. Bump the version in pyproject.toml first."
  exit 1
fi

echo "Creating tag $TAG..."
git tag "$TAG"

if $YES || ! [ -t 0 ]; then
  git push origin "$TAG"
  echo "Pushed $TAG."
else
  read -r -p "Push $TAG to origin? [y/N] " confirm
  if [[ "${confirm,,}" == "y" ]]; then
    git push origin "$TAG"
    echo "Pushed $TAG."
  else
    echo "Tag created locally. Run: git push origin $TAG"
  fi
fi
