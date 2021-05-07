#!/bin/bash
# ebi.sh $1 $2 $3
# $1 branch or tag docker image
# $2 steps to run
# $3 storage path : not mandatory
# Eg. ebi.sh master drug ot-snapshot/21.04
# Eg. ebi.sh 21.04 drug ot-snapshot/21.04/input
if [ -z "$1" ]
  then
    echo "No argument supplied"
  else
echo "Running on noah using lsf"
ssh noah-login <<EOF_A
cd /nfs/ftp/private/otftpuser/output_pis
cat > singularity_cmd.sh <<EOF_B
  cd /nfs/ftp/private/otftpuser/output_pis

  singularity exec \\
  -B /nfs/ftp/private/otftpuser/output_pis:/usr/src/app/output \\
  docker://quay.io/opentargets/platform-input-support:$1 \\
  conda run --no-capture-output -n pis-py3 python3 /usr/src/app/platform-input-support.py \\
  -gkey /homes/$USER/.config/gcloud/application_default_credentials.json \\
  -gb $3 -steps $2

  echo "Done" > /nfs/ftp/private/otftpuser/output_pis/lsf_done
  chmod -R 775 /nfs/ftp/private/otftpuser/output_pis/*

EOF_B
cat singularity_cmd.sh | bsub
EOF_A
fi
