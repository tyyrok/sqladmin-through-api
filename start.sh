#!/usr/bin/env bash
# -*- coding: utf-8 -*-
export ENVIRONMENT=local
export PYTHONDONTWRITEBYTECODE=1
template_env_a=.env.template.a
main_env_a=service-a/.env
template_env_b=.env.template.b
main_env_b=service-b/.env

if [[ ! -e ${main_env_a} ]]
then
    cp "${template_env_a}"  "${main_env_a}"
fi
if [[ ! -e ${main_env_b} ]]
then
    cp "${template_env_b}"  "${main_env_b}"
fi

docker compose -f docker/docker-compose-service-a.yml -f docker/docker-compose-service-b.yml up --build
docker compose -f docker/docker-compose-service-a.yml -f docker/docker-compose-service-b.yml
exit
