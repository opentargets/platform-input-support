#!/usr/bin/env bash

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

echo "Version: ${VERSION}"
echo "Version [major]: ${VERSION_MAJOR}"
echo "Version [minor]: ${VERSION_MINOR}"
echo "Version [patch]: ${VERSION_PATCH}"
echo "Version [pre-release]: ${VERSION_PRE_RELEASE}"

echo "Commit messages: ${COMMIT_MESSAGES}"
echo "Current tag: ${CURRENT_TAG}"
echo "New tag: ${NEW_TAG}"
