# This file contains helpers to work with the pipeline

# Syntactic sugar
alias l="ls -alh"
# PIS operational helpers
alias pis_logs_startup="sudo journalctl -u google-startup-scripts.service"
alias pis_logs_startup_tail="sudo journalctl -u google-startup-scripts.service -f"