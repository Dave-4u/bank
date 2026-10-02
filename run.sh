#!/usr/bin/env sh
# Console bank:        ./run.sh
# Tests:               ./run.sh test
# Browser version:     ./run.sh web   (then open http://localhost:8000)
cd "$(dirname "$0")"
case "$1" in
  test) exec python3 -m unittest discover -s tests -t . -v ;;
  web)  cd docs && exec python3 -m http.server 8000 ;;
  *)    exec python3 bank.py ;;
esac
