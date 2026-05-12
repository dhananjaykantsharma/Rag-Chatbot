import redis
import json
from langchain_core.messages import HumanMessage, AIMessage

redis_client = redis.Redis(
    host='localhost', 
    port=6379, 
    db=0, 
    decode_responses=True
)

def get_chat_history(user_id, limit=10):
    """Fetches the last `limit` messages for a given user_id from Redis. and return in langchain format"""
    key = f"chat_history:{user_id}"
    raw_history = redis_client.lrange(key, 0, limit - 1) 
    print(f"Raw history from Redis for user {user_id}: {raw_history}")
    messages = []
    for item in reversed(raw_history):
        data = json.loads(item)
        if data["role"] == "human":
            messages.append(HumanMessage(content=data["content"]))
        else:
            messages.append(AIMessage(content=data["content"]))

    print(f"Formatted messages for user {user_id}: {messages}")
    return messages

def add_message_to_history(user_id, role, content):
    """Adds a message to the user's chat history in Redis."""
    key = f"chat_history:{user_id}"
    payload = json.dumps({"role": role, "content": content})
    redis_client.lpush(key, payload)

    redis_client.ltrim(key, 0, 9)

    redis_client.expire(key, 86400)
