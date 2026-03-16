#!/bin/bash

## BASH script for including module
# Called from apps/docker/docker-build-dev.sh

MOD_LLM_CHATTER_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$MOD_LLM_CHATTER_ROOT/conf/mod_llm_chatter.conf" 2>/dev/null || true
