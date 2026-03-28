from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChatRepository:
    def __init__(self, db):
        self.sessions = db.chat_sessions
        self.messages = db.chat_messages

    def create_session(self, session_id: str, title: str, user_id: str):
        now = utc_now()
        self.sessions.insert_one({
            "session_id": session_id,
            "user_id": user_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
        })

    def get_session(self, session_id: str, user_id: str):
        return self.sessions.find_one(
            {"session_id": session_id, "user_id": user_id},
            {"_id": 0}
        )

    def touch_session(self, session_id: str, user_id: str):
        self.sessions.update_one(
            {"session_id": session_id, "user_id": user_id},
            {"$set": {"updated_at": utc_now()}}
        )

    def add_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        classifications=None,
        agents_used=None,
        pdf_url=None,
    ):
        self.messages.insert_one({
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "timestamp": utc_now(),
            "classifications": classifications or [],
            "agents_used": agents_used or [],
            "pdf_url": pdf_url,
        })

        self.touch_session(session_id, user_id)

    def list_sessions(self, user_id: str):
        return list(
            self.sessions.find(
                {"user_id": user_id},
                {"_id": 0}
            ).sort("updated_at", -1)
        )

    def get_messages(self, session_id: str, user_id: str):
        return list(
            self.messages.find(
                {"session_id": session_id, "user_id": user_id},
                {"_id": 0}
            ).sort("timestamp", 1)
        )

    def delete_chat(self, session_id: str, user_id: str):
        self.sessions.delete_one({"session_id": session_id, "user_id": user_id})
        self.messages.delete_many({"session_id": session_id, "user_id": user_id})