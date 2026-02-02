sudo apt update && sudo apt install -y curl

# installing uv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv init
uv add browser-use openai
uv sync