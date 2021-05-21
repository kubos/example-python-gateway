#!/usr/bin/env bash

if [ -d ./majortom_gateway_api ] 
then
  echo "Installing from local directory"
  pip install -e ./majortom_gateway_api
else
  echo "Installing from package manager" 
  pip install majortom_gateway
fi