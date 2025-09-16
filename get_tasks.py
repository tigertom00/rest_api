#!/usr/bin/env python3
"""
Get uncompleted tasks from the MCP server
"""
import asyncio
import json
import httpx

async def get_uncompleted_tasks():
    """Get uncompleted tasks from Django MCP server"""

    server_url = "http://127.0.0.1:8000/mcp/mcp"
    headers = {
        "Authorization": "Token f846237dce3d89f3d751027e3a12eb48c4bb3b9c",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    async with httpx.AsyncClient() as client:
        # Initialize session
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "task-client", "version": "1.0.0"}
            }
        }

        response = await client.post(server_url, json=init_payload, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to initialize: {response.text}")
            return

        session_id = response.headers.get("Mcp-Session-Id")
        if not session_id:
            print("❌ No session ID returned")
            return

        headers["Mcp-Session-Id"] = session_id

        # Query for uncompleted tasks
        query_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "query_data_collections",
                "arguments": {
                    "collection": "task",
                    "search_pipeline": [
                        {"$match": {"completed": False}},
                        {"$project": {
                            "title": 1,
                            "description": 1,
                            "status": 1,
                            "priority": 1,
                            "due_date": 1,
                            "created_at": 1
                        }},
                        {"$sort": {"priority": 1, "due_date": 1}}
                    ]
                }
            }
        }

        print("📋 Getting your uncompleted tasks...")
        response = await client.post(server_url, json=query_payload, headers=headers)

        if response.status_code == 200:
            result_data = response.json()
            print(f"Debug - Full response: {json.dumps(result_data, indent=2)}")

            content = result_data.get('result', {}).get('content', [])
            if not content:
                print("❌ No content in response")
                return

            tasks_json = content[0].get('text', '[]') if content else '[]'
            print(f"Debug - Tasks JSON: {tasks_json}")

            if not tasks_json or tasks_json.strip() == '':
                tasks = []
            else:
                tasks = json.loads(tasks_json)

            if not tasks:
                print("✅ No uncompleted tasks found! You're all caught up!")
                return

            print(f"\n🎯 Found {len(tasks)} uncompleted tasks:\n")

            for i, task in enumerate(tasks, 1):
                priority_emoji = {"high": "🔥", "medium": "⚡", "low": "📝"}.get(task.get("priority", "low"), "📝")
                status_emoji = {"todo": "⏳", "in_progress": "🔄", "completed": "✅"}.get(task.get("status", "todo"), "⏳")

                print(f"{i}. {priority_emoji} {status_emoji} {task.get('title', 'Untitled')}")

                if task.get('description'):
                    print(f"   📄 {task['description']}")

                if task.get('due_date'):
                    print(f"   📅 Due: {task['due_date']}")

                print(f"   🏷️  Status: {task.get('status', 'unknown').title()}")
                print(f"   ⚡ Priority: {task.get('priority', 'unknown').title()}")
                print()
        else:
            print(f"❌ Failed to get tasks: {response.text}")

if __name__ == "__main__":
    asyncio.run(get_uncompleted_tasks())