import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect('postgresql://root:123456@localhost:5432/host_light_food')
    rows = await conn.fetch('SELECT id, status, error_message, created_at FROM workflows ORDER BY created_at DESC LIMIT 5')
    result = []
    for row in rows:
        result.append({'id': str(row[0]), 'status': row[1], 'error': row[2], 'created': str(row[3])})
    await conn.close()
    with open('/Users/dogpay/work/ai-work/host-service/wf_result.json', 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

asyncio.run(main())
