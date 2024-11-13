#!/bin/sh

git filter-branch --commit-filter '
OLD_EMAIL="jaydentang418@gmail.com"
CORRECT_NAME="Jayden"
CORRECT_EMAIL="administrator418@users.noreply.github.com"
if [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_COMMITTER_NAME="$CORRECT_NAME"
    export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
fi' HEAD
