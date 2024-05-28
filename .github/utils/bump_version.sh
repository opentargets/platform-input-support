#!/bin/bash

VERSION="${CURRENT_TAG#[vV]}"
VERSION_MAJOR="${VERSION%%.*}"
VERSION_MINOR_PATCH="${VERSION#*.}"
VERSION_MINOR="${VERSION_MINOR_PATCH%%.*}"
VERSION_PATCH_PRE_RELEASE="${VERSION_MINOR_PATCH#*.}"
VERSION_PATCH="${VERSION_PATCH_PRE_RELEASE%%[-+]*}"
VERSION_PRE_RELEASE=""

case "$VERSION" in
  *-*)
    VERSION_PRE_RELEASE="${VERSION#*-}"
    VERSION_PRE_RELEASE="${VERSION_PRE_RELEASE%%+*}"
    ;;
esac

CHANGES=0

while IFS= read -r msg; do
  case "$msg" in
    "[MAJOR]"*)
      VERSION_MAJOR=$((VERSION_MAJOR + 1))
      CHANGES=$((CHANGES + 1))
      ;;
    "[MINOR]"*)
      VERSION_MINOR=$((VERSION_MINOR + 1))
      CHANGES=$((CHANGES + 1))
      ;;
          "[PATCH]"*)
      VERSION_PATCH=$((VERSION_PATCH + 1))
      CHANGES=$((CHANGES + 1))
      ;;
  esac
done <<< "$COMMIT_MESSAGES"

if [ "$CHANGES" -ne "1" ]; then
  >&2 echo "There must be EXACTLY ONE version bump in the commit messages. Something must be wrong."
  exit 1
else
  echo "${VERSION_MAJOR}.${VERSION_MINOR}.${VERSION_PATCH}${VERSION_PRE_RELEASE:+-$VERSION_PRE_RELEASE}"
fi
