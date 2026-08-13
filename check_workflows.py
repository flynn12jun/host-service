import asyncpg
import asyncio

async def main():
    conn = await asyncpg.connect('postgresql://root:123456@localhost:5432/host_light_food')
    rows = await conn.fetch('SELECT id, status, error_message, created_at FROM workflows ORDER BY created_at DESC LIMIT 5')
    
    with open('/Users/dogpay/work/ai-work/host-service/workflow_status.txt', 'w') as f:
        for row in rows:
            f.write(f"ID: {row['id']}\n")
            f.write(f"状态: {row['status']}\n")
            f.write(f"错误: {row['error_message']}\n")
            f.write(f"创建时间: {row['created_at']}\n")
            f.write('---\n')
    
    await conn.close()

asyncio.run(main())
