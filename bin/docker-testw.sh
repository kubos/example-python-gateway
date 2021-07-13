#!/bin/bash -e

cat << EOF

========================================================================
This creates a docker container and runs pytest-watch inside of it,
with the local directory bind-mounted. So you should be able to change
files locally and have the tests re-run automatically on each save.

If you create an entirely new file, you will have to restart this.
========================================================================

EOF

# For Dev -- Copy the latest dev gateway_api if that folder exists
if [ -d "../majortom_gateway_package" ]
then
  echo "Removing and re-copying gateway api"
  rm -rf majortom_gateway_api
  cp -R ../majortom_gateway_package majortom_gateway_api
fi

docker build -t example_gateway -f docker/Dockerfile.test .
docker run --rm -it \
  -v $(pwd):/app \
  example_gateway ptw --poll -- --verbose --capture=no --cache-clear