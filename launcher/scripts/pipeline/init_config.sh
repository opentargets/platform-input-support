#!/bin/bash

config_temp=$1
config_dest=$2

# Setup destination dir
cp $config_temp $config_dest
# Replace values
sed -i.bak \
    -e "s/<EFO_RELEASE_VERSION>/$OTOPS_EFO_RELEASE_VERSION/g" \
    -e "s/<ENSEMBL_RELEASE_VERSION>/$OTOPS_ENSEMBL_RELEASE_VERSION/g" \
    -e "s/<CHEMBL_RELEASE_VERSION>/$OTOPS_CHEMBL_RELEASE_VERSION/g" \
    -- "${config_dest}" && 
    rm -- "${config_dest}.bak"