#!/bin/bash

set -e

git remote update

UPSTREAM=master

LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse "$UPSTREAM")
BASE=$(git merge-base @ "$UPSTREAM")

updatePelisalaceppa(){
	git checkout master
	git pull
	git subtree split --prefix=python/main-classic -b pelisalacarta
	git checkout pelisalaceppa
	git merge pelisalacarta

	echo "Done! You need to push"
}

if [ $LOCAL = $REMOTE ]; then
    echo "Up-to-date"
elif [ $LOCAL = $BASE ]; then
    updatePelisalaceppa
elif [ $REMOTE = $BASE ]; then
    echo "Need to push"
else
    echo "Diverged"
fi
