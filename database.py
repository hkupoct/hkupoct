import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

engine = None

if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )


def init_database():
    if not engine:
        print("⚠️ DATABASE_URL not found. Database is disabled.")
        return

    with engine.begin() as connection:

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                profile_name TEXT NOT NULL,
                user_name TEXT,
                city TEXT,
                state TEXT,
                unread_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user_id, profile_name)
            )
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL,
                message_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (conversation_id)
                REFERENCES conversations(id)
                ON DELETE CASCADE
            )
        """))

        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_conversations_updated
            ON conversations(updated_at DESC)
        """))

        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages(conversation_id, created_at)
        """))

    print("✅ PostgreSQL database initialized successfully")

def get_or_create_conversation(
    user_id,
    profile_name,
    user_name,
    city,
    state
):
    if not engine:
        return None

    with engine.begin() as connection:

        result = connection.execute(
            text("""
                INSERT INTO conversations
                (
                    user_id,
                    profile_name,
                    user_name,
                    city,
                    state
                )
                VALUES
                (
                    :user_id,
                    :profile_name,
                    :user_name,
                    :city,
                    :state
                )

                ON CONFLICT (user_id, profile_name)
                DO UPDATE SET
                    user_name = EXCLUDED.user_name,
                    city = EXCLUDED.city,
                    state = EXCLUDED.state,
                    updated_at = CURRENT_TIMESTAMP

                RETURNING id
            """),
            {
                "user_id": user_id,
                "profile_name": profile_name,
                "user_name": user_name,
                "city": city,
                "state": state
            }
        )

        return result.scalar_one()


def save_chat_message(conversation_id, sender_type, message_text):
    if not engine:
        return

    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO messages (
                conversation_id,
                sender_type,
                message_text
            )
            VALUES (
                :conversation_id,
                :sender_type,
                :message_text
            )
        """), {
            "conversation_id": conversation_id,
            "sender_type": sender_type,
            "message_text": message_text
        })

        # Only USER messages should increase unread count
        if sender_type == "user":
            connection.execute(text("""
                UPDATE conversations
                SET unread_count = unread_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :conversation_id
            """), {
                "conversation_id": conversation_id
            })
        else:
            connection.execute(text("""
                UPDATE conversations
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = :conversation_id
            """), {
                "conversation_id": conversation_id
            })


def mark_conversation_read(conversation_id):
    if not engine:
        return

    with engine.begin() as connection:

        connection.execute(
            text("""
                UPDATE conversations
                SET
                    unread_count = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :conversation_id
            """),
            {
                "conversation_id": conversation_id
            }
        )

def get_admin_conversations(limit=20):
    if not engine:
        return []

    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                c.id,
                c.user_id,
                c.profile_name,
                c.user_name,
                c.city,
                c.state,
                c.unread_count,
                c.updated_at,
                (
                    SELECT m.message_text
                    FROM messages m
                    WHERE m.conversation_id = c.id
                    ORDER BY m.created_at DESC, m.id DESC
                    LIMIT 1
                ) AS latest_message
            FROM conversations c
            ORDER BY c.updated_at DESC
            LIMIT :limit
        """), {"limit": limit})

        return [dict(row._mapping) for row in result]

def get_admin_conversation_by_id(conversation_id):
    if not engine:
        return None

    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                id,
                user_id,
                profile_name,
                user_name,
                city,
                state,
                unread_count,
                created_at,
                updated_at
            FROM conversations
            WHERE id = :conversation_id
        """), {
            "conversation_id": conversation_id
        })

        row = result.fetchone()

        if not row:
            return None

        conversation = dict(row._mapping)

        message_result = connection.execute(text("""
            SELECT
                sender_type,
                message_text,
                created_at
            FROM messages
            WHERE conversation_id = :conversation_id
            ORDER BY created_at ASC, id ASC
        """), {
            "conversation_id": conversation_id
        })

        conversation["messages"] = [
            {
                "sender": row.sender_type,
                "text": row.message_text,
                "created_at": row.created_at
            }
            for row in message_result
        ]

        return conversation

def get_conversation_id(user_id, profile_name):
    if not engine:
        return None

    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT id
            FROM conversations
            WHERE user_id = :user_id
              AND profile_name = :profile_name
            LIMIT 1
        """), {
            "user_id": user_id,
            "profile_name": profile_name
        })

        row = result.fetchone()

        if not row:
            return None

        return row.id
