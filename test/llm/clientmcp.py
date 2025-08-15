import asyncio

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from openai import AsyncOpenAI


async def ask_lm_studio(prompt: str):
    async with AsyncOpenAI(
        api_key="lm-studio",
        base_url="http://hour-checking.gl.at.ply.gg:45843/v1"
    ) as api:
        resp = await api.chat.completions.create(
            model="CrazyMita",
            messages=[{"role": "user", "content": prompt}],
            functions=[{
                "name": "two_plus_two",
                "description": "Вычисляет 2 + 2",
                "parameters": {}
            }],
            function_call="two_plus_two"  # модель решает, когда вызвать функцию
        )
        return resp.choices[0].message

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["/home/miku/dev/MitAIbot/test/llm/srvermcp.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Доступные тулзы:", tools)

            # Просим модель что-то посчитать
            message = await ask_lm_studio("Вычисли 2 + 2")

            # Если модель решила вызвать функцию
            if message.function_call is not None:
                func_name = message.function_call.name
                arguments = message.function_call.arguments or {}

                result = await session.call_tool(func_name, arguments=arguments)
                print(f"Модель вызвала {func_name}: {result.structuredContent['result']}")
            else:
                print("Ответ от LM Studio:", message.content)

asyncio.run(main())
