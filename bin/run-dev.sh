#!/bin/bash -e

# For Dev -- Copy the gateway_api
if [ -d "../majortom_gateway_package" ]
then
  echo "Removing and re-copying gateway api"
  rm -rf majortom_gateway_api
  cp -R ../majortom_gateway_package majortom_gateway_api
else
  echo "This is a development script. You must have the gateway api cloned in ../majortom_gateway_package"
fi

cat << EOF

========================================================================
                    Running the Dockerized Gateway in Dev

Usage:
  run-dev.sh [-h] [-b BASICAUTH] [-l {info,error}] [--http] majortomhost gatewaytoken

Example:
  ./run-dev.sh host.docker.internal:3001 7e74c854c7250a55fca087d3636580822648c528e7aa401f034e038c1a61e63b --http -l info

Notes:
 - If connecting to localhost, use "host.docker.internal" instead of localhost or 127.0.0.1
 - This dev environment expects the majortom_gateway_package to be cloned in a sister directory.
 
========================================================================

EOF

docker build -t gateway_dev .
docker run --rm -it \
    gateway_dev "$@"

