#!/usr/bin/env bash
failed=0
for t in tests/t*.py; do
  echo "▶ $t"
  if ! python3 "$t"; then
    failed=___
  fi
done
if [ "$failed" -ne 0 ]; then
  echo "SOME TESTS FAILED"
  exit 1
fi
echo "ALL TESTS PASSED"
