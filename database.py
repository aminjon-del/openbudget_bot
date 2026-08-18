import asyncpg
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

pool = None

async def create_pool():
    global pool
    pool = await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        min_size=5,
        max_size=50
    )

async def init_db():
    async with pool.acquire() as conn:
        # Foydalanuvchilar jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL, -- 'Pullik agent' yoki 'Volontyor'
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        # Ovozlar jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                phone VARCHAR(20) NOT NULL,
                status VARCHAR(30) DEFAULT 'Jarayonda', -- 'Qabul qilindi', 'Rad etildi', 'Jarayonda'
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

async def add_user(user_id, full_name, role):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, full_name, role)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET full_name = $2, role = $3;
        """, user_id, full_name, role)

async def get_user(user_id):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE user_id = $1;", user_id)

async def add_vote(user_id, phone, status="Jarayonda"):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO votes (user_id, phone, status)
            VALUES ($1, $2, $3)
            RETURNING id;
        """, user_id, phone, status)
        return row['id']

async def update_vote_status(vote_id, status):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE votes SET status = $1 WHERE id = $2;", status, vote_id)
        return await conn.fetchrow("SELECT * FROM votes WHERE id = $1;", vote_id)

async def get_agent_stats(user_id):
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT status, COUNT(*) as count 
            FROM votes 
            WHERE user_id = $1 
            GROUP BY status;
        """, user_id)
        return {r['status']: r['count'] for r in rows}

async def get_top_30():
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT u.full_name, u.role, COUNT(v.id) as confirmed_count
            FROM users u
            JOIN votes v ON u.user_id = v.user_id
            WHERE v.status = 'Qabul qilindi'
            GROUP BY u.user_id, u.full_name, u.role
            ORDER BY confirmed_count DESC
            LIMIT 30;
        """)

async def get_paid_agents_report():
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT v.id, v.created_at, u.full_name, v.phone, v.status
            FROM votes v
            JOIN users u ON v.user_id = u.user_id
            WHERE u.role = 'Pullik agent'
            ORDER BY v.created_at DESC;
        """)