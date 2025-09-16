#!/usr/bin/env python3
"""
Simple MCP client to test the Django MCP server
"""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import httpx

async def test_mcp_server():
    """Test the Django MCP server via HTTP"""

    # Server URL and auth
    server_url = "http://127.0.0.1:8000/mcp/mcp"
    headers = {
        "Authorization": "Token f846237dce3d89f3d751027e3a12eb48c4bb3b9c",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    async with httpx.AsyncClient(cookies={}, follow_redirects=True) as client:
        # Try to initialize session
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        print("🚀 Initializing MCP session...")
        response = await client.post(server_url, json=init_payload, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            # Get session ID from response headers
            session_id = response.headers.get("Mcp-Session-Id")
            if session_id:
                print(f"📋 Session ID: {session_id}")
                # Add session ID to headers for subsequent requests
                headers["Mcp-Session-Id"] = session_id

                # Try to list tools
                list_tools_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }

                print("\n🔧 Listing available tools...")
                response = await client.post(server_url, json=list_tools_payload, headers=headers)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    tools_data = response.json()
                    print(f"Found {len(tools_data.get('result', {}).get('tools', []))} tools")
                    for tool in tools_data.get('result', {}).get('tools', [])[:3]:  # Show first 3
                        print(f"  - {tool['name']}: {tool['description']}")
                else:
                    print(f"Response: {response.text}")

                if response.status_code == 200:
                    # Try to call a simple tool
                    query_payload = {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": "query_data_collections",
                            "arguments": {
                                "collection": "customuser",
                                "search_pipeline": [{"$limit": 2}]
                            }
                        }
                    }

                    print("\n📊 Querying user data...")
                    response = await client.post(server_url, json=query_payload, headers=headers)
                    print(f"Status: {response.status_code}")
                    if response.status_code == 200:
                        result_data = response.json()
                        print("✅ Query successful!")
                        print(f"Result: {json.dumps(result_data.get('result'), indent=2)}")
                    else:
                        print(f"Response: {response.text}")
            else:
                print("❌ No session ID returned from initialization")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())