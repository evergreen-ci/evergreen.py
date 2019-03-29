#!/usr/bin/env bash


if [ -z "$1" ]; then
    echo "Missing PyPi username"
    exit 1
fi

if [ -z "$2" ]; then
    echo "Missing PyPi password"
    exit 1
fi

username=$1
password=$2


if [ -e "dist" ]; then
    echo "dist directory already exists, exiting"
    exit 2
fi

python setup.py sdist bdist_wheel
rc=$?
if [ $rc -ne 0 ]; then
    echo "Error building distribution"
    exit 3
fi

twine upload --username $username --password $password dist/*
exit $?
