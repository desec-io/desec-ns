#!/bin/sh
if ! test -f "$HOME"/.ssh/id_ed25519; then
  ssh-keygen -N "" -ted25519  -f "$HOME"/.ssh/id_ed25519
  echo 'New Public Key generated!'
  cat "$HOME"/.ssh/id_ed25519.pub
fi
echo "$DESECSTACK_SSH_KNOWN_HOST" > "$HOME"/.ssh/known_hosts
exec python -u run.py
