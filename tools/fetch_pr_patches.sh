#!/usr/bin/env bash
# Download the patch files a pull request adds or changes, as data only (no PR code
# is checked out or run). Usage: fetch_pr_patches.sh PR_NUMBER DEST_DIR
# Prints the paths of any non-patch files the PR touches to stderr.
set -euo pipefail
pr="$1"; dest="$2"; repo="${GITHUB_REPOSITORY:?}"
mkdir -p "$dest"
head_repo=$(gh api "repos/$repo/pulls/$pr" -q .head.repo.full_name)
head_sha=$(gh api "repos/$repo/pulls/$pr" -q .head.sha)
gh api "repos/$repo/pulls/$pr/files" --paginate -q '.[] | select(.status != "removed") | .filename' |
while read -r path; do
  if [[ "$path" =~ ^data/patches/pending/[^/]+\.ya?ml$ ]]; then
    gh api -H "Accept: application/vnd.github.raw" "repos/$head_repo/contents/$path?ref=$head_sha" > "$dest/$(basename "$path")"
  else
    echo "$path" >&2
  fi
done
