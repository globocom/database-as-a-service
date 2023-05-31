#!/bin/bash
source .env

echo "Usando o user:${USER_GCP}"
ssh ${USER_GCP}@${DBAAS_VM_DEV} << SSHREMOTE
echo 'start'
sudo -H -u docker bash -c 'cd /home/docker && source ./prepare_variables_dbaas.sh; docker compose -f docker-compose-host-provider.yml up -dsource ./prepare_variables_dbaas.sh; docker compose -f docker-compose-dbaas.yml up -d'
echo 'fim'
SSHREMOTE