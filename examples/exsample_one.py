import asyncio
from liara import LiaraAPI


API_KEY = "ABCDEFGHIJKLMNOPQ"

async def main():
    async with LiaraAPI(API_KEY) as app:
        data = await app.list_projects()
        print(data)


if __name__ == "__main__":
    asyncio.run(main())