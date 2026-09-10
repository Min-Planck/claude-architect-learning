# Claude Architect Learning

A learning repository for mastering Anthropic Claude's Messages API, Agentic Architectures, and Tool Use Patterns, preparing for production-grade AI agents.

---

## Overview

This repository provides modular, episode-based implementations of core architectural patterns using Anthropic's Claude models. Each episode pairs conceptual documentation (`note.md`) with a runnable Python implementation (`example.py`).```

## Getting Started

### Prerequisites
- **Python**: `>= 3.11`
- **Package Manager**: [`uv`](https://github.com/astral-sh/uv) (recommended) or standard `pip`
- **Anthropic API Key**: Obtain one from [console.anthropic.com](https://console.anthropic.com/)

---

### Installation & Environment Setup

Using `uv`:

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd claude-architect-learning
   ```

2. **Sync dependencies and create virtual environment:**
   ```bash
   uv sync
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and supply your Anthropic API credentials:
   ```env
   ANTHROPIC_API_KEY="your-anthropic-api-key-here"
   MODEL="claude-haiku-4-5"
   MAX_LOOP_ITERATIONS=50
   ```

---

## Running the Code

### 1. Verify API Connectivity
Run the health check script to ensure your API key and model access are working:

```bash
# Using uv
uv run api_health_check.py
```

### 2. Run Episode 01: Agentic Loop
Execute the weather agent loop example:

```bash
# Using uv
uv run python ep_01_agentic_loop_and_stop_reason/example.py

# Using standard Python
python ep_01_agentic_loop_and_stop_reason/example.py
```

## License

This repository is maintained for educational and architectural reference purposes.
