import asyncio
import asyncpg
import json

async def main():
    try:
        conn = await asyncpg.connect('postgresql://root:123456@localhost:5432/host_light_food')
        rows = await conn.fetch('SELECT id, status, error_message, created_at FROM workflows ORDER BY created_at DESC LIMIT 5')
        result = [{'id': str(r[0]), 'status': r[1], 'error': r[2], 'created': str(r[3])} for r in rows]
        await conn.close()
        with open('/Users/dogpay/work/ai-work/host-service/wf.json', 'w') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception as e:
        with open('/Users/dogpay/work/ai-work/host-service/wf.json', 'w') as f:
            json.dump({'error': str(e)}, f)

asyncio.run(main())
