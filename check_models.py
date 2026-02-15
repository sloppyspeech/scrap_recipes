
import asyncio
from backend.ollama_client import list_models

async def main():
    models = await list_models()
    print(models)

if __name__ == "__main__":
    asyncio.run(main())
