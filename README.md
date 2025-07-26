# MCP4Meme 🚀

FastMCP demo server for meme-related functionality.

## Features

### Bonding Curve & Token Analysis
- **Bonding curve progress**: Track token graduation status (0-100%)
- **Migration tracking**: Monitor token migration from bonding curve to DEX
- **Token lifecycle**: Identify tokens approaching "graduation" threshold

### Trading & Market Data  
- **Latest trades**: Real-time trading activity and transaction history
- **Price data**: Current USD and BNB prices with market cap
- **Volume analytics**: Trading volume statistics with OHLCV data
- **Market trends**: Price movements and trading patterns

### Trader & Liquidity Analysis
- **Top traders**: Identify high-volume traders and "smart money"
- **Liquidity events**: Track liquidity additions/removals
- **Trading behavior**: Analyze trader patterns and P&L

### Discovery & Search
- **Progress search**: Find tokens by bonding curve completion (e.g., 90-95%)
- **Trending tokens**: Discover hot tokens by volume, trades, or progress
- **Market scanning**: Search across Four.meme ecosystem

### Demo Tools (Legacy)
- **Calculator tools**: `add()`, `multiply()` 
- **Greeting tool**: `get_greeting(name)`

## Quick Start

### Local Development

```bash
# Install dependencies
uv pip install -r requirements.txt

# Configure API key (optional - uses mock data without key)
cp .env.example .env
# Edit .env and add your Bitquery API key

# Run server
python mcp_server.py

# Test with FastMCP inspector
fastmcp dev mcp_server.py
```

### Docker Usage

```bash
# Build image
docker build -t mcp4meme .

# STDIO mode (for MCP clients)
docker run -it mcp4meme

# With API key
docker run -it -e BITQUERY_API_KEY=your_key_here mcp4meme

# HTTP mode (for web access)
docker run -p 8000:8000 mcp4meme python mcp_server.py --http

# Using docker-compose
docker-compose up mcp4meme
docker-compose --profile http up mcp4meme-http
```

### DeepChat Integration

**With API key (real data):**
```json
{
  "mcpServers": {
    "mcp4meme": {
      "command": "docker",
      "args": ["run", "-i", "mcp4meme"],
      "env": {
        "BITQUERY_API_KEY": "your_bitquery_api_key_here"
      }
    }
  }
}
```

**Without API key (mock data):**
```json
{
  "mcpServers": {
    "mcp4meme": {
      "command": "docker",
      "args": ["run", "-i", "mcp4meme"]
    }
  }
}
```

## Available Tools

### Bonding Curve & Token Analysis
- `get_bonding_curve_progress(token_address: str)` - Get token bonding curve progress percentage
- `get_token_migration_status(token_address: str)` - Check token migration status from bonding curve to DEX

### Trading & Market Data
- `get_latest_trades(token_address: str, limit: int = 10)` - Get latest trading records
- `get_token_price_usd(token_address: str)` - Get current USD price for a token
- `get_trading_volume(token_address: str, timeframe: str = "24h")` - Get trading volume statistics

### Trader & Liquidity Analysis  
- `get_top_traders(token_address: str, limit: int = 10, timeframe: str = "24h")` - Get top traders by volume
- `get_liquidity_events(token_address: str, limit: int = 10)` - Get liquidity-related events

### Discovery & Search
- `search_tokens_by_progress(min_progress: float = 90.0, max_progress: float = 95.0, limit: int = 20)` - Search tokens by bonding curve progress
- `get_trending_tokens(timeframe: str = "24h", sort_by: str = "volume", limit: int = 10)` - Get trending tokens

### Demo Tools (Legacy)
- `add(a: int, b: int) -> int` - Add two numbers
- `multiply(a: int, b: int) -> int` - Multiply two numbers  
- `get_greeting(name: str) -> str` - Get a personalized greeting

## Resources

- `config://mcp4meme` - Server configuration and features
- `config://fourmeme-proxy` - Four.meme proxy contract configuration

## API Configuration

The server uses the Bitquery API to fetch blockchain data. To use real data:

1. Get a free API key from [Bitquery.io](https://bitquery.io/)
2. Copy `.env.example` to `.env`
3. Add your API key: `BITQUERY_API_KEY=your_key_here`

Without an API key, the server returns mock data for testing.
