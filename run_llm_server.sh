#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-"$ROOT_DIR/llama.cpp"}"
MODEL_DIR="${MODEL_DIR:-"$ROOT_DIR/models"}"
MODEL_FILE="${MODEL_FILE:-Huihui-Qwen3-VL-2B-Instruct-abliterated.Q4_K_M.gguf}"
MODEL_PATH="$MODEL_DIR/$MODEL_FILE"

if [ ! -d "$LLAMA_CPP_DIR" ]; then
  git clone https://github.com/ggerganov/llama.cpp "$LLAMA_CPP_DIR"
  cd "$LLAMA_CPP_DIR"
  make LLAMA_CUBLAS=1
else
  cd "$LLAMA_CPP_DIR"
fi

mkdir -p "$MODEL_DIR"
if [ ! -f "$MODEL_PATH" ]; then
  if ! command -v huggingface-cli >/dev/null 2>&1; then
    echo "huggingface-cli not found; install it first" >&2
    exit 1
  fi
  huggingface-cli download mradermacher/Huihui-Qwen3-VL-2B-Instruct-abliterated-GGUF \
    --filename "$MODEL_FILE" \
    --local-dir "$MODEL_DIR"
fi

./server -m "$MODEL_PATH" --host 127.0.0.1 --port 8000 --ctx-size 4096 --batch 8 --ngl 999




