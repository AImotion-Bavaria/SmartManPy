#!/usr/bin/env bash
if [[ ${CODEBUILD_GIT_TAG%-*} =~ ^[0-9]+\.[0-9]+\.[0-9]+ ]]; then
    make release
else
    echo "Skipping release"
fi
