#!/bin/bash -e

cat << EOF

========================================================================
                         Running the Dockerized Gateway

Usage:
  run-docker.sh [-h] [-b BASICAUTH] [-l {info,error}] [--http] [-a|--async] majortomhost gatewaytoken

Example:
  ./run-docker.sh app.majortom.cloud:3001 d722811cc115d8321821cbb3dde56b367c2346d766468d288b39b301254ee2ac

  # Example for staging
  ./run-docker.sh staging2.testing.majortom.cloud/ df907812f7007029ad895a594d55bc08fa3745b0b1bb28094dd4c83d2957f714 -b staging2:STAGING_PASSWORD

  # Example for local
  ./run-docker.sh host.docker.internal:3001 df907812f7007029ad895a594d55bc08fa3745b0b1bb28094dd4c83d2957f714 --http

========================================================================

EOF

docker build -t gateway .
docker run --rm -it \
    gateway "$@"

