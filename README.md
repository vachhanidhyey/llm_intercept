# LLM Intercept

A proxy server that intercepts and stores calls to large language models (LLMs) for building fine-tuning datasets for small, efficient models. Perfect for training compact models like [Liquid AI's LFM2 series](https://huggingface.co/collections/LiquidAI/lfm2-686d721927015b2ad73eaa38) (350M to 2.6B parameters) using data from larger models.

The steps are as simple as:

1. Use a LLM in your app via an OpenAI-compatible API to solve your task.
2. Run traffic through LLM Intercept (this package) to log the data
3. Export the dataset directly as parquet and with system prompts removed (optional)
4. Fine-tune a smaller model on the collected data
5. Replace the large model with your fine-tuned small model much cheaper/faster or locally at zero cost
6. Profit!

Works with any OpenAI-compatible API including OpenRouter, other API providers, and local LLM servers.

## Key Features

- 🎯 **Ready for fine-tuning** - Automatically formats conversations with assistant responses for direct model training
- 🔄 **OpenAI-compatible API** - Drop-in replacement for OpenAI API clients
- 🌐 **API agnostic** - Works with OpenRouter, llama.cpp (llama-server), and any OpenAI-compatible endpoint
- 📊 **Request logging** - Stores all requests and responses in SQLite database
- 🌊 **Streaming support** - Full support for SSE streaming responses
- 🔧 **Function calls** - Supports OpenAI function calling and tools
- 📈 **Admin dashboard** - Web interface for viewing and analyzing stored requests
- 📦 **Export functionality** - Export as JSONL.zstd or Parquet format for ML pipelines
- 🔍 **Search & filter** - Filter by date, model, and search message content
- 🔐 **Password protected** - Admin interface secured with password authentication

> **⚠️ Legal Disclaimer**
> Users are responsible for ensuring compliance with the terms of service of their model provider regarding fine-tuning on model outputs. Some proprietary models (e.g., OpenAI, Anthropic) may restrict this usage. We recommend using open-source models with permissive licenses such as:
> - **DeepSeek-V3.2** (MIT License)
> - **Qwen3-235B-A22B** (Apache 2.0)
> - **GLM-4.5** (MIT License)
> - Other Apache 2.0 / MIT licensed models
>
> Always review your provider's terms before collecting training data.

## Installation

```bash
pip install llm-intercept
```

Or install from source for development:

```bash
git clone https://github.com/yourusername/llm-intercept.git
cd llm-intercept
pip install -e ".[dev]"
```

## Quick Start

### 1. Start the server

```bash
# Using OpenRouter (default)
llm-intercept serve --admin-password YOUR_SECURE_PASSWORD

# Using OpenRouter (manual)
llm-intercept serve \
  --base-url https://openrouter.ai/api/v1/chat/completions \
  --admin-password YOUR_SECURE_PASSWORD

# Using a local Ollama server
llm-intercept serve \
  --base-url http://localhost:11434/v1/chat/completions \
  --admin-password YOUR_SECURE_PASSWORD
```

Or using environment variables:

```bash
export BASE_URL=https://openrouter.ai/api/v1/chat/completions
export ADMIN_PASSWORD=YOUR_SECURE_PASSWORD
llm-intercept serve
```

The server will start on `http://localhost:8000` by default.

### 2. Use the proxy in your application

Simply point your OpenAI-compatible client to the proxy server:

```python
import openai


client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-api-key"  # e.g., OpenRouter key
)

response = client.chat.completions.create(
    model="deepseek/deepseek-chat-v3.1",  # Use appropriate model for your target API
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)
```

### 3. View collected data

Access the admin dashboard at:
```
http://localhost:8000/admin?password=YOUR_SECURE_PASSWORD
```

## CLI Reference

### `llm-intercept serve`

Start the proxy server.

**Options:**
- `--host` - Host to bind to (default: `0.0.0.0`)
- `--port` - Port to bind to (default: `8000`)
- `--base-url` - Target API base URL (default: `https://openrouter.ai/api/v1/chat/completions`, can use `BASE_URL` env var)
- `--database-url` - Database URL (default: `sqlite:///./llm_intercept.db`)
- `--admin-password` - Admin interface password (required, can use `ADMIN_PASSWORD` env var)
- `--reload` - Enable auto-reload for development

**Examples:**

```bash
# Basic usage (OpenRouter)
llm-intercept serve --admin-password mypassword

# Custom host and port
llm-intercept serve --host 127.0.0.1 --port 5000 --admin-password mypassword

# Development mode with auto-reload
llm-intercept serve --admin-password mypassword --reload
```

### `llm-intercept init-database`

Initialize the database (create tables).

**Options:**
- `--database-url` - Database URL (default: `sqlite:///./llm_intercept.db`)

**Example:**

```bash
llm-intercept init-database --database-url sqlite:///./my_data.db
```

## API Endpoints

### `/v1/chat/completions` (POST)

OpenAI-compatible chat completions endpoint. Forwards requests to the configured target API and stores them.

**Headers:**
- `Authorization: Bearer YOUR_API_KEY` (API key for your target service)

**Supported parameters:**
- `model` - Model identifier (e.g., `deepseek/deepseek-chat-v3.1`)
- `messages` - Array of message objects
- `temperature` - Sampling temperature
- `max_tokens` - Maximum tokens to generate
- `top_p` - Nucleus sampling parameter
- `frequency_penalty` - Frequency penalty
- `presence_penalty` - Presence penalty
- `stream` - Enable streaming (boolean)
- `functions` - Function definitions (OpenAI format)
- `function_call` - Function call parameter
- `tools` - Tool definitions (OpenAI format)
- `tool_choice` - Tool choice parameter

### `/health` (GET)

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00"
}
```

### `/admin` (GET)

Admin dashboard interface (password protected).

**Query parameters:**
- `password` - Admin password (required)

## Admin Dashboard Features

### Statistics
- Total requests count
- Unique models used
- Average response time

### Filtering
- **Date range** - Filter by start and end datetime
- **Model** - Filter by specific model
- **Text search** - Search within message content

### Viewing Requests
- Paginated list of requests (20 per page)
- Color-coded status indicators (green=OK, red=error)
- View full conversation messages (including assistant responses)
- View tool calls separately if present
- View raw API response data
- See metadata (timestamp, model, response time, streaming status)

### Export Data
- **Format options**: JSONL.zstd or Parquet
- **Auto-filtering**: Only exports successful requests (status='ok')
- Option to include or exclude system prompts
- Download button generates timestamped file
- Ready for ML pipelines and fine-tuning frameworks

### Export Formats

**JSONL.zstd** - One JSON object per line, compressed:
```json
{
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ],
  "model": "deepseek/deepseek-chat-v3.1",
  "timestamp": "2024-01-01T12:00:00",
  "tool_calls": [...]  // Optional, if present
}
```

**Parquet** - Columnar format with snappy compression:
- `messages` - JSON string of conversation array
- `model` - Model identifier
- `timestamp` - ISO timestamp
- `tool_calls` - JSON string of tool calls (nullable)

## Database Schema

The package uses SQLModel with SQLite by default. The main table `llm_requests` stores:

- Request metadata (timestamp, model, API key hash)
- Sampling parameters (temperature, max_tokens, etc.)
- Messages (JSON)
- Response data (JSON)
- Performance metrics (response_time_ms)
- Error information (if any)

## Environment Variables

- `BASE_URL` - Target API base URL (default: `https://openrouter.ai/api/v1/chat/completions`)
- `DATABASE_URL` - Database connection URL (default: `sqlite:///./llm_intercept.db`)
- `ADMIN_PASSWORD` - Password for admin interface (required)

## Use Cases

### Fine-tuning Dataset Collection

1. Build an application using a large, expensive model (e.g., DeepSeek, Qwen3)
2. Route all API calls through LLM Intercept proxy
3. Collect real-world usage data
4. Export the dataset
5. Fine-tune a smaller, cheaper model (e.g., LFM2-1.2B)
6. Deploy the fine-tuned model locally or at lower cost

### API Monitoring

- Track model usage across your organization
- Monitor response times and errors
- Analyze prompt patterns
- Debug API issues

### Cost Analysis

- Compare different models' performance
- Track token usage
- Identify optimization opportunities

## Development

### Running tests

```bash
pip install -e ".[dev]"
pytest
```

### Code formatting

```bash
black llm_intercept/
ruff check llm_intercept/
```

## License

MIT license. See `LICENSE` file for details.

---

<sub>This app was vibe-coded with Claude Code (Sonnet 4.5) in under an hour. No guarantees, no warranties, use at your own risk! 🚀</sub>

