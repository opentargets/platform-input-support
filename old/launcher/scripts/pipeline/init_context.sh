#!/bin/bash
# Iterate over all variables in config_profile.sh that start with OTOPS and 'echo' the variable name and value
for var in $(env | grep ^OTOPS_ | cut -d= -f1); do
    echo "export ${var}=${!var}"
done