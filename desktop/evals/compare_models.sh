#!/usr/bin/env bash
# Runs Fauve's eval suite on several local models, one after another, and prints a
# league table at the end. Leave it running; everything stays on this Mac except the
# one-time model downloads from Hugging Face.
#
# Usage (from the fauve repo, venv active, your normal model server STOPPED):
#   caffeinate -i bash desktop/evals/compare_models.sh
#
# Each model gets its own server on port 8081, which is stopped before the next one.

set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
PORT=8081
LOG="$HERE/compare_$(date +%Y%m%d-%H%M).log"

MODELS=(
  "mlx-community/Qwen3.5-9B-MLX-4bit"     # current model (baseline)
  "mlx-community/Qwen3.5-9B-MLX-8bit"     # same model, less compressed: slower, maybe better
  "mlx-community/Qwen3.5-4B-MLX-4bit"     # smaller: faster, maybe worse
)

echo "Fauve model comparison · $(date)" | tee "$LOG"
SERVER=""
cleanup() { [ -n "$SERVER" ] && kill "$SERVER" 2>/dev/null; }
trap cleanup EXIT

for MODEL in "${MODELS[@]}"; do
  echo "" | tee -a "$LOG"
  echo "=== $MODEL ===" | tee -a "$LOG"
  mlx_lm.server --model "$MODEL" --host 127.0.0.1 --port "$PORT" >>"$LOG.server" 2>&1 &
  SERVER=$!

  # wait for the server (first run downloads the model: allow up to 60 minutes)
  READY=0
  for _ in $(seq 1 720); do
    if curl -s "http://127.0.0.1:$PORT/v1/models" >/dev/null 2>&1; then READY=1; break; fi
    if ! kill -0 "$SERVER" 2>/dev/null; then break; fi
    sleep 5
  done
  if [ "$READY" != 1 ]; then
    echo "  server didn't start for $MODEL (see $LOG.server), skipping" | tee -a "$LOG"
    kill "$SERVER" 2>/dev/null; SERVER=""; continue
  fi

  python3 "$HERE/run_evals.py" --url "http://127.0.0.1:$PORT" --model "$MODEL" --timeout 600 2>&1 | tee -a "$LOG"

  kill "$SERVER" 2>/dev/null; wait "$SERVER" 2>/dev/null; SERVER=""
  sleep 5
done

echo "" | tee -a "$LOG"
echo "=== League table ===" | tee -a "$LOG"
grep -E "^=== |TOTAL" "$LOG" | grep -v "League" | tee -a "$LOG.table"
echo "" ; echo "Full log: $LOG"