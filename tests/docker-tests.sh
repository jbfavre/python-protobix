#!/bin/bash

VERSION=$(sed 's/\..*//' /etc/debian_version)
case ${VERSION} in
  7) echo 'Debian Wheezy'
     packages_list='python2.7 python-setuptools python-configobj python-simplejson python-pytest python-mock adduser'
     test_suite_list='python'
     ;;
  8) echo 'Debian Jessie'
     packages_list='python2.7 python3 python-setuptools python3-setuptools python-configobj python-simplejson python3-configobj python3-simplejson python-pytest python-pytest-cov python-mock python3-pytest python3-pytest-cov python3-mock'
     test_suite_list='python python3'
     ;;
  *) echo 'Debian stretch/sid'
     packages_list='python2.7 python3 python-setuptools python3-setuptools python-configobj python-simplejson python3-configobj python3-simplejson python-pytest python-pytest-cov python-mock python3-pytest python3-pytest-cov python3-mock'
     test_suite_list='python python3'
     ;;
esac

function cleanup() {
    cd /home/python-protobix
    find . -name '*.pyc' -exec rm {} \; 2>/dev/null
    find . -name '__pycache__' -exec rm -r {} \; 2>/dev/null
}

# Update package list
apt-get update

# Install dependencies for both python 2.7 & python 3
apt-get -qy install ${packages_list}

# Create an unprivileged user
addgroup -gid 1000 protobix
adduser --system -uid 1000 -gid 1000 --home /home/python-protobix \
        --shell /bin/bash --no-create-home --disabled-password \
        protobix


for test_suite in ${test_suite_list}
do
    # Clean existing cache files
    cleanup
    # Run test suite
    su - protobix -s /bin/bash -c "cd /home/python-protobix;${test_suite} setup.py test"
done

# Clean existing cache files
cleanup
