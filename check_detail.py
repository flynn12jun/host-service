import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect('postgresql://root:123456@localhost:5432/host_light_food')
    
    # 获取最新工作流的详细信息
    row = await conn.fetchrow('''
        SELECT id, status, error_message, customer_input, 
               director_output, nutritionist_output, rd_chef_output, head_chef_output,
               created_at, updated_at
        FROM workflows 
        ORDER BY created_at DESC 
        LIMIT 1
    ''')
    
    if row:
        result = {
            'id': str(row[0]),
            'status': row[1],
            'error': row[2],
            'customer_input': row[3],
            'director_output': row[4],
            'nutritionist_output': row[5],
            'rd_chef_output': row[6],
            'head_chef_output': row[7],
            'created': str(row[8]),
            'updated': str(row[9]),
        }
        with open('/Users/dogpay/work/ai-work/host-service/wf_detail.json', 'w') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Status: {row[1]}")
        print(f"Error: {row[2]}")
        print(f"Customer Input: {row[3]}")
    else:
        print("No workflows found")
    
    await conn.close()

asyncio.run(main())
