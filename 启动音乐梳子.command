#!/bin/zsh
cd "${0:A:h}"
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv || exit 1
  .venv/bin/python -m pip install -r requirements.txt || exit 1
fi
if /usr/bin/curl --fail --silent http://127.0.0.1:8818/api/catalog >/dev/null; then
  open http://127.0.0.1:8818
  exit 0
fi
(sleep 1; open http://127.0.0.1:8818) &
.venv/bin/python -m comb serve --port 8818
