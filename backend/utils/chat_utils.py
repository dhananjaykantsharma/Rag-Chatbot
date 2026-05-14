import json
from models import ChatHistory
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from utils.redis_util import add_message_to_history
from database import SessionLocal
import asyncio

def map_history(history_list):
    messages = []
    for msg in history_list:
        # 1. AGAR MESSAGE PEHLE SE HI LANGCHAIN OBJECT HAI (Fix for your error)
        if isinstance(msg, BaseMessage):
            messages.append(msg)
            continue

        # 2. AGAR MESSAGE DICTIONARY HAI
        try:
            if isinstance(msg, str):
                data = json.loads(msg)
            elif isinstance(msg, dict):
                data = msg
            else:
                print(f"Unknown message type: {type(msg)}")
                continue
            
            role = data.get("role")
            content = data.get("content")
            
            if role in ["human", "user"]:
                messages.append(HumanMessage(content=content))
            elif role in ["ai", "assistant"]:
                messages.append(AIMessage(content=content))
        except Exception as e:
            print(f"Error parsing history message: {e}")
            continue
            
    return messages


async def generate_answer(chunks, chat_id, user_id, question):
    full_answer = ""
    db = SessionLocal()
    try:
        async for content in chunks:
            # Note: StrOutputParser makes 'content' a direct string
            if content:
                full_answer += content
                yield content
                await asyncio.sleep(0.01)

        # Success: Redis and DB storage
        add_message_to_history(user_id, "human", question)
        add_message_to_history(user_id, "ai", full_answer)

        chat_entry = db.query(ChatHistory).filter(ChatHistory.id == chat_id).first()
        if chat_entry:
            chat_entry.answer = full_answer
            chat_entry.status = "completed"
            db.commit()

    except Exception as e:
        print(f"Streaming Error inside generator: {e}")
        yield f"\n[Error: {str(e)}]"
    finally:
        db.close()
