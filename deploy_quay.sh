#!/bin/bash
set -ev
if [ "${TRAVIS_PULL_REQUEST}" = "false" ] || [ "${TRAVIS_TAG}" != "" ]; then
  docker build .
  docker login -u="${QUAY_USER}" -p="${QUAY_PASSWORD}" quay.io
  docker tag "${QUAY_REPO}" "${QUAY_REPO}:${TRAVIS_TAG}"
  docker push "${QUAY_REPO}:${TRAVIS_TAG}"
  if [ "${TRAVIS_BRANCH}" = "master" ]; then
    docker tag "${QUAY_REPO}" "${QUAY_REPO}:latest"
    docker push "${QUAY_REPO}:latest"
  fi
fi