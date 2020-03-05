#!/bin/bash

# Fail hard when anything fails
set -e
set -o pipefail

# OpenLDAP / lmdb release, and associated checksum
VERSION=2.4.49
CHECKSUM=f0caeca122e6f90e6ac5cc8ba36fe9cec13826da

# Fetch source package and verify checksum
wget https://www.openldap.org/software/download/OpenLDAP/openldap-release/openldap-${VERSION}.tgz && sha1sum -c <<< "$CHECKSUM openldap-${VERSION}.tgz"

tar xzf openldap-${VERSION}.tgz
cd openldap-${VERSION}/libraries/liblmdb/
make && make DESTDIR=/tmp/stage install
