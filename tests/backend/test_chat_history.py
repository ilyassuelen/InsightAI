from __future__ import annotations

import tests as _test_bootstrap  # noqa: F401  # configure isolated services first
import unittest

from backend.database.database import SessionLocal
from backend.models.chat_conversation import ChatConversation
from backend.models.chat_message import ChatMessage
from backend.models.document import Document
from tests.support import create_document, create_user_workspace, reset_database


class ChatHistoryLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.user, self.workspace = create_user_workspace()

    def test_deleting_document_cascades_document_chat_history(self) -> None:
        document = create_document(
            self.workspace.id,
            self.user.id,
            filename="private.txt",
        )
        db = SessionLocal()
        try:
            conversation = ChatConversation(
                workspace_id=self.workspace.id,
                document_id=document.id,
                created_by_user_id=self.user.id,
                title="Private document chat",
            )
            db.add(conversation)
            db.flush()
            db.add(
                ChatMessage(
                    conversation_id=conversation.id,
                    role="user",
                    content="Question",
                    sequence_index=0,
                )
            )
            db.commit()
            conversation_id = conversation.id

            stored_document = (
                db.query(Document)
                .filter(Document.id == document.id)
                .one()
            )
            db.delete(stored_document)
            db.commit()

            self.assertIsNone(
                db.query(ChatConversation)
                .filter(ChatConversation.id == conversation_id)
                .first()
            )
            self.assertEqual(
                db.query(ChatMessage)
                .filter(ChatMessage.conversation_id == conversation_id)
                .count(),
                0,
            )
        finally:
            db.close()

if __name__ == "__main__":
    unittest.main()
