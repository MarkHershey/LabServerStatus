#!/usr/bin/env bash

# update pip
printf "\n>>> pip install --upgrade pip wheel setuptools \n"
pip install --upgrade pip wheel setuptools
printf ">>> OK \n"


# install project dependencies
printf "\n>>> pip install project dependencies...\n"
pip install --upgrade puts==0.0.7 pydantic fastapi uvicorn 
printf ">>> OK \n"