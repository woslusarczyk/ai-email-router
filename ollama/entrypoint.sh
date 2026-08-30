#!/bin/sh
set -e

MODEL_NAME="${MODEL_NAME:-llama3.2}"

ollama serve &
SERVE_PID=$!

until ollama list >/dev/null 2>&1; do
  sleep 1
done

if ! ollama list | grep -q "$MODEL_NAME"; then
  ollama pull "$MODEL_NAME"
fi

wait $SERVE_PID
