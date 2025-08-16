import asyncio
from liara import LiaraAPI

API_KEY = "ABCDEFGHIJKLMNOPQ"

async def main():
    client = LiaraAPI(API_KEY)
    data = await client.list_projects()
    print(data)

if __name__ == "__main__":
    asyncio.run(main())