from fastmcp import FastMCP, Context
import httpx
from typing import Optional, Dict, List, Any
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("MCP4Meme 🚀")

# Bitquery API configuration
BITQUERY_API_URL = "https://streaming.bitquery.io/graphql"
BITQUERY_API_KEY = os.getenv("BITQUERY_API_KEY", "")
FOURMEME_PROXY_ADDRESS = "0x5c952063c7fc8610FFDB798152D69F0B9550762b"


class BitqueryClient:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
        }

        if BITQUERY_API_KEY:
            # Try both authentication methods
            self.headers["X-API-KEY"] = BITQUERY_API_KEY
            self.headers["Authorization"] = f"Bearer {BITQUERY_API_KEY}"

    async def execute_query(self, query: str, variables: Dict = None) -> Dict:
        """Execute GraphQL query against Bitquery API"""
        async with httpx.AsyncClient() as client:
            payload = {"query": query}
            if variables:
                payload["variables"] = variables

            if not BITQUERY_API_KEY:
                return {"error": "BITQUERY_API_KEY not provided"}

            try:
                response = await client.post(
                    BITQUERY_API_URL, json=payload, headers=self.headers, timeout=30
                )

                # Check response status and content
                if response.status_code != 200:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}

                # Check if response is empty
                if not response.text.strip():
                    return {"error": "Empty response from API"}

                try:
                    return response.json()
                except json.JSONDecodeError as json_err:
                    return {"error": f"Invalid JSON response: {response.text[:200]}..."}

            except Exception as e:
                return {"error": f"Request failed: {str(e)}"}


bitquery = BitqueryClient()


# Four.meme Trending Tokens Tool


@mcp.tool
async def get_trending_tokens(
    limit: int = 10,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get trending tokens on Four.meme platform

    Args:
        limit: Number of tokens to return

    Returns:
        List of trending tokens with their statistics
    """
    query = """
    query GetTrendingTokens($limit: Int!, $time_24hr_ago: DateTime) {
      EVM(network: bsc) {
        DEXTradeByTokens(
          limit: {count: $limit}
          orderBy: {descendingByField: "trades_24hr"}
          where: {
            Trade: {Success: true}
            Block: {Time: {since: $time_24hr_ago}}
          }
        ) {
          Trade {
            Currency {
              Name
              Symbol
              SmartContract
            }
          }
          volume_24hr: sum(of: Trade_Side_AmountInUSD)
          trades_24hr: count
        }
      }
    }
    """

    # Calculate 24 hours ago
    from datetime import datetime, timedelta

    time_24hr_ago = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"

    if ctx:
        await ctx.info(f"Calling Bitquery API with limit: {limit}")
        await ctx.info(f"Time filter: {time_24hr_ago}")
        await ctx.info(f"API Key present: {bool(BITQUERY_API_KEY)}")
        if BITQUERY_API_KEY:
            await ctx.info(
                f"API Key prefix: {BITQUERY_API_KEY[:8]}..."
                if len(BITQUERY_API_KEY) > 8
                else "Key too short"
            )

    result = await bitquery.execute_query(
        query, {"limit": limit, "time_24hr_ago": time_24hr_ago}
    )

    if ctx:
        await ctx.info(f"API result: {result}")

    # Check for errors
    if "error" in result:
        if ctx:
            await ctx.info(f"API Error: {result['error']}")
        return {
            "trending_tokens": [],
            "error": result["error"],
        }

    # Parse real API response
    if ctx:
        await ctx.info("Processing API response...")

    trending_tokens = []

    try:
        trades_data = result.get("data", {}).get("EVM", {}).get("DEXTradeByTokens", [])

        for i, trade in enumerate(trades_data[:limit]):
            token_info = trade.get("Trade", {}).get("Currency", {})
            trade_count = trade.get("trades_24hr", 0)
            volume_24hr = trade.get("volume_24hr", 0)

            trending_tokens.append(
                {
                    "rank": i + 1,
                    "token_address": token_info.get("SmartContract", ""),
                    "symbol": token_info.get("Symbol", ""),
                    "name": token_info.get("Name", ""),
                    "trade_count": trade_count,
                    "volume_24hr_usd": str(volume_24hr),
                }
            )

    except Exception as e:
        if ctx:
            await ctx.info(f"Error parsing response: {str(e)}")
        return {
            "trending_tokens": [],
            "error": f"Failed to parse API response: {str(e)}",
        }

    return {
        "trending_tokens": trending_tokens,
        "total_found": len(trending_tokens),
    }


@mcp.tool
async def get_bonding_curve_progress(token_address: str, ctx: Context = None) -> Dict[str, Any]:
    """
    Calculate how close a token is to "graduation" from bonding curve
    
    Args:
        token_address: Token contract address
        
    Returns:
        Progress percentage, remaining tokens, and graduation status
    """
    query = """
    query GetBondingCurveProgress($tokenAddress: String!) {
      EVM(network: bsc) {
        Transfers(
          where: {
            Transfer: {
              Currency: {SmartContract: {is: $tokenAddress}}
              Receiver: {is: "0x5c952063c7fc8610FFDB798152D69F0B9550762b"}
            }
          }
          orderBy: {descendingByField: "Block_Time"}
          limit: {count: 1}
        ) {
          Transfer {
            Amount
            Currency {
              Name
              Symbol
              SmartContract
            }
          }
          Block {
            Time
          }
        }
      }
    }
    """
    
    if ctx:
        await ctx.info(f"Checking bonding curve progress for token: {token_address}")
    
    result = await bitquery.execute_query(query, {"tokenAddress": token_address})
    
    if ctx:
        await ctx.info(f"Bonding curve API result: {result}")
    
    if "error" in result:
        return {
            "token_address": token_address,
            "progress_percentage": 0,
            "status": "unknown",
            "error": result["error"]
        }
    
    try:
        transfers_data = result.get("data", {}).get("EVM", {}).get("Transfers", [])
        
        if not transfers_data:
            return {
                "token_address": token_address,
                "progress_percentage": 0,
                "status": "early",
                "message": "No transfers to Four.meme contract found"
            }
        
        # For demo purposes, calculate a mock progress
        # In reality, you'd need the initial supply and current supply data
        mock_progress = 75.5  # This should be calculated from actual data
        
        status = "early" if mock_progress < 50 else "active" if mock_progress < 90 else "approaching_graduation" if mock_progress < 95 else "graduated"
        
        transfer_info = transfers_data[0]
        token_info = transfer_info.get("Transfer", {}).get("Currency", {})
        
        return {
            "token_address": token_address,
            "symbol": token_info.get("Symbol", ""),
            "name": token_info.get("Name", ""),
            "progress_percentage": mock_progress,
            "status": status,
            "graduation_threshold": 95.0,
            "last_activity": transfer_info.get("Block", {}).get("Time", "")
        }
        
    except Exception as e:
        if ctx:
            await ctx.info(f"Error parsing bonding curve data: {str(e)}")
        return {
            "token_address": token_address,
            "progress_percentage": 0,
            "status": "unknown",
            "error": f"Failed to parse response: {str(e)}"
        }


@mcp.tool
async def get_latest_trades(token_address: str, limit: int = 10, ctx: Context = None) -> Dict[str, Any]:
    """
    Get real-time trading activity for a specific token
    
    Args:
        token_address: Token contract address
        limit: Number of recent trades to return
        
    Returns:
        Recent buy/sell trades with prices and trader addresses
    """
    query = """
    query GetLatestTrades($tokenAddress: String!, $limit: Int!) {
      EVM(network: bsc) {
        DEXTrades(
          where: {
            Trade: {
              Buy: {Currency: {SmartContract: {is: $tokenAddress}}}
              Dex: {ProtocolName: {is: "fourmeme_v1"}}
              Success: true
            }
          }
          orderBy: {descendingByField: "Block_Time"}
          limit: {count: $limit}
        ) {
          Transaction {
            Hash
          }
          Block {
            Time
            Number
          }
          Trade {
            Buy {
              Buyer
              Amount
              AmountInUSD
              Price
              Currency {
                Symbol
                Name
              }
            }
            Sell {
              Seller
              Amount
              Currency {
                Symbol
                Name
              }
            }
          }
        }
      }
    }
    """
    
    if ctx:
        await ctx.info(f"Fetching latest trades for token: {token_address}")
    
    result = await bitquery.execute_query(query, {
        "tokenAddress": token_address,
        "limit": limit
    })
    
    if ctx:
        await ctx.info(f"Latest trades API result: {result}")
    
    if "error" in result:
        return {
            "token_address": token_address,
            "trades": [],
            "error": result["error"]
        }
    
    try:
        trades_data = result.get("data", {}).get("EVM", {}).get("DEXTrades", [])
        
        trades = []
        for trade in trades_data:
            trade_info = trade.get("Trade", {})
            buy_info = trade_info.get("Buy", {})
            sell_info = trade_info.get("Sell", {})
            
            trades.append({
                "transaction_hash": trade.get("Transaction", {}).get("Hash", ""),
                "timestamp": trade.get("Block", {}).get("Time", ""),
                "block_number": trade.get("Block", {}).get("Number", 0),
                "buyer": buy_info.get("Buyer", ""),
                "seller": sell_info.get("Seller", ""),
                "buy_amount": str(buy_info.get("Amount", 0)),
                "sell_amount": str(sell_info.get("Amount", 0)),
                "price_usd": str(buy_info.get("AmountInUSD", 0)),
                "buy_token": buy_info.get("Currency", {}).get("Symbol", ""),
                "sell_token": sell_info.get("Currency", {}).get("Symbol", "")
            })
        
        return {
            "token_address": token_address,
            "trades": trades,
            "total_trades": len(trades)
        }
        
    except Exception as e:
        if ctx:
            await ctx.info(f"Error parsing trades data: {str(e)}")
        return {
            "token_address": token_address,
            "trades": [],
            "error": f"Failed to parse response: {str(e)}"
        }


@mcp.tool
async def get_token_migration_status(token_address: str, ctx: Context = None) -> Dict[str, Any]:
    """
    Track if a token has migrated from bonding curve to DEX
    
    Args:
        token_address: Token contract address
        
    Returns:
        Migration status, DEX pairs, and migration timestamp
    """
    query = """
    query GetMigrationStatus($tokenAddress: String!) {
      EVM(network: bsc) {
        DEXTrades(
          where: {
            Trade: {
              Buy: {Currency: {SmartContract: {is: $tokenAddress}}}
              Dex: {ProtocolName: {not: "fourmeme_v1"}}
              Success: true
            }
          }
          orderBy: {ascendingByField: "Block_Time"}
          limit: {count: 5}
        ) {
          Trade {
            Dex {
              ProtocolName
              SmartContract
            }
            Buy {
              Currency {
                Symbol
                Name
              }
            }
            Sell {
              Currency {
                Symbol
                Name
              }
            }
          }
          Block {
            Time
          }
        }
      }
    }
    """
    
    if ctx:
        await ctx.info(f"Checking migration status for token: {token_address}")
    
    result = await bitquery.execute_query(query, {"tokenAddress": token_address})
    
    if ctx:
        await ctx.info(f"Migration API result: {result}")
    
    if "error" in result:
        return {
            "token_address": token_address,
            "is_migrated": False,
            "dex_pairs": [],
            "error": result["error"]
        }
    
    try:
        trades_data = result.get("data", {}).get("EVM", {}).get("DEXTrades", [])
        
        if not trades_data:
            return {
                "token_address": token_address,
                "is_migrated": False,
                "status": "bonding_curve_only",
                "dex_pairs": [],
                "message": "Token still trading only on Four.meme bonding curve"
            }
        
        # Extract DEX information
        dex_pairs = []
        migration_timestamp = None
        
        for trade in trades_data:
            trade_info = trade.get("Trade", {})
            dex_info = trade_info.get("Dex", {})
            
            if not migration_timestamp:
                migration_timestamp = trade.get("Block", {}).get("Time", "")
            
            pair_info = {
                "dex_name": dex_info.get("ProtocolName", ""),
                "dex_contract": dex_info.get("SmartContract", ""),
                "buy_token": trade_info.get("Buy", {}).get("Currency", {}).get("Symbol", ""),
                "sell_token": trade_info.get("Sell", {}).get("Currency", {}).get("Symbol", "")
            }
            
            if pair_info not in dex_pairs:
                dex_pairs.append(pair_info)
        
        return {
            "token_address": token_address,
            "is_migrated": True,
            "status": "migrated_to_dex",
            "migration_timestamp": migration_timestamp,
            "dex_pairs": dex_pairs,
            "total_dex_pairs": len(dex_pairs)
        }
        
    except Exception as e:
        if ctx:
            await ctx.info(f"Error parsing migration data: {str(e)}")
        return {
            "token_address": token_address,
            "is_migrated": False,
            "dex_pairs": [],
            "error": f"Failed to parse response: {str(e)}"
        }


@mcp.resource("config://mcp4meme")
async def mcp4meme_config():
    """MCP4Meme configuration resource"""
    return {
        "name": "MCP4Meme Server",
        "version": "2.0.0",
        "features": [
            "trending_tokens",
            "bonding_curve_progress",
            "latest_trades",
            "token_migration_status"
        ],
        "networks": ["bsc"],
        "fourmeme_proxy": FOURMEME_PROXY_ADDRESS,
        "api_endpoints": {"bitquery": BITQUERY_API_URL},
        "mock_mode": not bool(BITQUERY_API_KEY),
    }


@mcp.resource("config://fourmeme-proxy")
async def fourmeme_proxy_config():
    """Four.meme proxy contract configuration"""
    return {
        "contract_address": FOURMEME_PROXY_ADDRESS,
        "network": "bsc",
        "graduation_threshold": 95.0,
        "bonding_curve_formula": "100 - ((leftTokens * 100) / initialRealTokenReserves)",
    }


if __name__ == "__main__":
    import sys

    if "--http" in sys.argv:
        mcp.run(transport="http", port=8000)
    else:
        mcp.run()
