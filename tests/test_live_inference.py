"""
Live Ollama Inference and SSE Stream Verification Script.
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Offline env
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["OLLAMA_NO_USAGE_STATS"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.db import init_db
from backend.chat_mode import handle_chat_mode
from backend.code_mode import handle_code_mode
from backend.router import route_message


async def main():
    init_db()
    print("=== Testing Live Chat Mode ===")
    events = []
    async for event in handle_chat_mode("live_test_chat", "Hello, can you confirm what is 2+2?"):
        events.append(event)
        if "token" in event:
            sys.stdout.write(event["token"])
            sys.stdout.flush()
    print(f"\nFinal event: {events[-1]}\n")

    print("=== Testing Live Code Mode ===")
    code_events = []
    async for event in handle_code_mode("live_test_code", "Write a python script to calculate the sum of numbers from 1 to 10."):
        code_events.append(event)
        if "token" in event:
            sys.stdout.write(event["token"])
            sys.stdout.flush()
    print(f"\nFinal event: {code_events[-1]}\n")
    print("=== All Live Inferences Succeeded! ===")


if __name__ == "__main__":
    asyncio.run(main())
