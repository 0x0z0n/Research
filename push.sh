#!/bin/bash


if [ -z "$1" ]
then
  echo "Error: No commit message provided."
  echo "Usage: ./push.sh 'Your commit message'"
  exit 1
fi

git add .
git commit -m "$1"
git push origin main
