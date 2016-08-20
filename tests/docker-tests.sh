#!/bin/bash

function cleanup() {
    cd /home/python-protobix
    find . -name '*.pyc' -exec rm {} \; 2>/dev/null
    find . -name '__pycache__' -exec rm -r {} \; 2>/dev/null
}

# Create un privileged user
addgroup -gid 1000 protobix
adduser --system -uid 1000 -gid 1000 --home /home/python-protobix \
        --shell /bin/bash --no-create-home --disabled-password \
        protobix

# Update package list
apt-get update

# Install dependencies for both python 2.7 & python 3
apt-get -qy install python2.7 python3 python-setuptools python3-setuptools
apt-get -qy install python-configobj python-simplejson python3-configobj python3-simplejson
apt-get -qy install python-pytest python-pytest-cov python-mock
apt-get -qy install python3-pytest python3-pytest-cov python3-mock

# Clean existing cache files
cleanup

# Run test suite for bot python 2.7 & python 3
su - protobix -s /bin/bash -c 'cd /home/python-protobix;python setup.py test'
su - protobix -s /bin/bash -c 'cd /home/python-protobix;python3 setup.py test'

# Clean existing cache files
cleanup
