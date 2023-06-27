#!/usr/bin/env bash

# make callable from anywhere
cd "$( dirname "${BASH_SOURCE[0]}" )"

tmux new-session \; \
  send-keys './ripDVD_handbrake.py -d 0' C-m \; \
  split-window -v \; \
  send-keys './ripDVD_handbrake.py -d 1' C-m \; \
  split-window -v \; \
  send-keys './ripDVD_handbrake.py -d 2' C-m \; \

# tmux new-session \; \
#   send-keys 'echo  0' C-m \; \
#   split-window -v \; \
#   send-keys 'echo  1' C-m \; \
#   split-window -v \; \
#   send-keys C-b M-2 \; \
