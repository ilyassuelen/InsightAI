from __future__ import annotations

import tests as _test_bootstrap  # noqa: F401  # configure isolated services first
import unittest
import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.database.database import SessionLocal
from backend.main import app
from backend.models.document import Document
from backend.models.report import Report
from backend.models.user import User
from backend.models.workspace import Workspace
from backend.models.workspace_member import WorkspaceMember
from backend.services.auth.jwt import create_access_token
from backend.services.storage import upload_validation
from tests.support import auth_headers, create_document, reset_database


class AuthWorkspaceApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        reset_database()
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

        cls.alice_password = "StrongPassword123!"
        cls.bob_password = "AnotherPassword123!"
        alice_response = cls.client.post(
            "/auth/register",
            json={"email": "alice@example.test", "password": cls.alice_password, "full_name": "Alice"},
        )
        bob_response = cls.client.post(
            "/auth/register",
            json={"email": "bob@example.test", "password": cls.bob_password, "full_name": "Bob"},
        )
        if alice_response.status_code != 200 or bob_response.status_code != 200:
            raise AssertionError((alice_response.text, bob_response.text))
        cls.alice = alice_response.json()
        cls.bob = bob_response.json()
        cls.alice_headers = auth_headers(cls.alice["access_token"])
        cls.bob_headers = auth_headers(cls.bob["access_token"])

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_context.__exit__(None, None, None)

    def _personal_workspace_id(self, headers: dict[str, str]) -> int:
        response = self.client.get("/workspaces/", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        return next(item["id"] for item in response.json() if item["type"] == "personal")

    def _user_id(self, email: str) -> int:
        db = SessionLocal()
        try:
            return db.query(User).filter(User.email == email).one().id
        finally:
            db.close()

    def test_root_health_endpoint(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "InsightAI is running!"})

    def test_auth_register_login_me_and_validation(self) -> None:
        duplicate = self.client.post(
            "/auth/register",
            json={"email": "ALICE@example.test", "password": self.alice_password},
        )
        self.assertEqual(duplicate.status_code, 409)

        short = self.client.post(
            "/auth/register",
            json={"email": "short@example.test", "password": "short"},
        )
        self.assertEqual(short.status_code, 400)

        bad_login = self.client.post(
            "/auth/login",
            json={"email": "alice@example.test", "password": "wrong-password"},
        )
        self.assertEqual(bad_login.status_code, 401)

        login = self.client.post(
            "/auth/login",
            json={"email": " Alice@Example.Test ", "password": self.alice_password},
        )
        self.assertEqual(login.status_code, 200)
        me = self.client.get("/auth/me", headers=auth_headers(login.json()["access_token"]))
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["email"], "alice@example.test")

        self.assertEqual(self.client.get("/auth/me").status_code, 401)

    @unittest.expectedFailure
    def test_invalid_email_format_is_rejected(self) -> None:
        response = self.client.post(
            "/auth/register",
            json={"email": f"invalid email {uuid.uuid4().hex}", "password": "StrongPassword123!"},
        )
        self.assertIn(response.status_code, {400, 422})

    @unittest.expectedFailure
    def test_refresh_type_token_is_rejected_by_authenticated_endpoint(self) -> None:
        token = create_access_token(subject=str(self.alice["user_id"]), extra={"type": "refresh"})
        response = self.client.get("/auth/me", headers=auth_headers(token))
        self.assertEqual(response.status_code, 401)

    def test_personal_workspace_exists_and_cannot_be_deleted(self) -> None:
        workspace_id = self._personal_workspace_id(self.alice_headers)
        members = self.client.get(f"/workspaces/{workspace_id}/members", headers=self.alice_headers)
        self.assertEqual(members.status_code, 200)
        self.assertEqual(members.json()[0]["role"], "owner")
        deleted = self.client.delete(f"/workspaces/{workspace_id}", headers=self.alice_headers)
        self.assertEqual(deleted.status_code, 400)

    def test_team_workspace_membership_and_owner_permissions(self) -> None:
        name = f"Team {uuid.uuid4().hex[:8]}"
        created = self.client.post("/workspaces/", headers=self.alice_headers, json={"name": name})
        self.assertEqual(created.status_code, 200, created.text)
        workspace_id = created.json()["id"]

        added = self.client.post(
            f"/workspaces/{workspace_id}/members",
            headers=self.alice_headers,
            json={"email": "bob@example.test", "role": "member"},
        )
        self.assertEqual(added.status_code, 200, added.text)

        bob_workspaces = self.client.get("/workspaces/", headers=self.bob_headers)
        self.assertIn(workspace_id, [item["id"] for item in bob_workspaces.json()])

        forbidden_rename = self.client.patch(
            f"/workspaces/{workspace_id}",
            headers=self.bob_headers,
            json={"name": "Bob Rename"},
        )
        self.assertEqual(forbidden_rename.status_code, 403)

        renamed = self.client.patch(
            f"/workspaces/{workspace_id}",
            headers=self.alice_headers,
            json={"name": "Renamed Team"},
        )
        self.assertEqual(renamed.status_code, 200)
        self.assertEqual(renamed.json()["name"], "Renamed Team")

        bob_id = self._user_id("bob@example.test")
        removed = self.client.delete(
            f"/workspaces/{workspace_id}/members/{bob_id}",
            headers=self.alice_headers,
        )
        self.assertEqual(removed.status_code, 200)

    @unittest.expectedFailure
    def test_team_workspace_can_be_deleted_without_fk_error(self) -> None:
        created = self.client.post(
            "/workspaces/",
            headers=self.alice_headers,
            json={"name": f"Delete {uuid.uuid4().hex[:8]}"},
        )
        workspace_id = created.json()["id"]
        deleted = self.client.delete(f"/workspaces/{workspace_id}", headers=self.alice_headers)
        self.assertEqual(deleted.status_code, 200)

    @unittest.expectedFailure
    def test_member_cannot_be_promoted_to_second_owner(self) -> None:
        created = self.client.post(
            "/workspaces/",
            headers=self.alice_headers,
            json={"name": f"Roles {uuid.uuid4().hex[:8]}"},
        )
        workspace_id = created.json()["id"]
        promoted = self.client.post(
            f"/workspaces/{workspace_id}/members",
            headers=self.alice_headers,
            json={"email": "bob@example.test", "role": "owner"},
        )
        self.assertEqual(promoted.status_code, 400)

    def test_document_and_report_are_workspace_isolated(self) -> None:
        alice_workspace = self._personal_workspace_id(self.alice_headers)
        alice_id = self._user_id("alice@example.test")
        document = create_document(alice_workspace, alice_id, filename=f"private-{uuid.uuid4().hex}.txt")

        own = self.client.get(f"/documents/{document.id}", headers=self.alice_headers)
        foreign = self.client.get(f"/documents/{document.id}", headers=self.bob_headers)
        self.assertEqual(own.status_code, 200)
        self.assertEqual(foreign.status_code, 403)

        db = SessionLocal()
        try:
            report = Report(
                document_id=document.id,
                content={"title": "Private", "summary": "S", "sections": [], "conclusion": "C"},
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            report_id = report.id
        finally:
            db.close()

        own_report = self.client.get(f"/reports/{document.id}", headers=self.alice_headers)
        foreign_report = self.client.get(f"/reports/{document.id}", headers=self.bob_headers)
        foreign_delete = self.client.delete(f"/reports/{report_id}", headers=self.bob_headers)
        self.assertEqual(own_report.status_code, 200)
        self.assertEqual(own_report.json()["title"], "Private")
        self.assertEqual(foreign_report.status_code, 403)
        self.assertEqual(foreign_delete.status_code, 403)

    def test_chat_validates_workspace_document_relationship_before_llm(self) -> None:
        alice_workspace = self._personal_workspace_id(self.alice_headers)
        bob_workspace = self._personal_workspace_id(self.bob_headers)
        alice_id = self._user_id("alice@example.test")
        document = create_document(alice_workspace, alice_id, filename=f"chat-{uuid.uuid4().hex}.txt")

        with patch("backend.routers.chat.generate_chat_response", new=AsyncMock(return_value="Grounded")) as generate:
            valid = self.client.post(
                "/chat/",
                headers=self.alice_headers,
                json={"message": "Question", "workspace_id": alice_workspace, "document_id": document.id},
            )
            mismatch = self.client.post(
                "/chat/",
                headers=self.bob_headers,
                json={"message": "Question", "workspace_id": bob_workspace, "document_id": document.id},
            )

        self.assertEqual(valid.status_code, 200)
        self.assertEqual(valid.json()["answer"], "Grounded")
        self.assertIsInstance(valid.json()["conversation_id"], int)
        self.assertEqual(mismatch.status_code, 400)
        generate.assert_awaited_once()

    def test_chat_does_not_leak_internal_exception_text(self) -> None:
        workspace = self._personal_workspace_id(self.alice_headers)
        secret = "internal-secret-token-123"
        with patch(
            "backend.routers.chat.generate_chat_response",
            new=AsyncMock(side_effect=RuntimeError(secret)),
        ):
            response = self.client.post(
                "/chat/",
                headers=self.alice_headers,
                json={"message": "Question", "workspace_id": workspace, "document_id": None},
            )
        self.assertEqual(response.status_code, 500)
        self.assertNotIn(secret, response.text)

    def test_chat_conversation_is_persisted_reloaded_and_private(self) -> None:
        workspace = self._personal_workspace_id(self.alice_headers)
        alice_id = self._user_id("alice@example.test")
        document = create_document(
            workspace,
            alice_id,
            filename=f"history-{uuid.uuid4().hex}.txt",
        )
        generate = AsyncMock(side_effect=["First answer", "Second answer"])

        with patch(
            "backend.routers.chat.generate_chat_response",
            new=generate,
        ):
            first = self.client.post(
                "/chat/",
                headers=self.alice_headers,
                json={
                    "message": "First question",
                    "workspace_id": workspace,
                    "document_id": document.id,
                },
            )
            conversation_id = first.json()["conversation_id"]
            second = self.client.post(
                "/chat/",
                headers=self.alice_headers,
                json={
                    "message": "Follow-up question",
                    "workspace_id": workspace,
                    "document_id": document.id,
                    "conversation_id": conversation_id,
                },
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["conversation_id"], conversation_id)
        self.assertEqual(generate.await_count, 2)
        self.assertEqual(generate.await_args_list[0].kwargs["history"], [])
        self.assertEqual(
            generate.await_args_list[1].kwargs["history"],
            [
                {"role": "user", "content": "First question"},
                {"role": "assistant", "content": "First answer"},
            ],
        )

        conversations = self.client.get(
            "/chat/conversations",
            headers=self.alice_headers,
            params={"workspace_id": workspace, "document_id": document.id},
        )
        self.assertEqual(conversations.status_code, 200)
        self.assertIn(
            conversation_id,
            [item["id"] for item in conversations.json()],
        )

        detail = self.client.get(
            f"/chat/conversations/{conversation_id}",
            headers=self.alice_headers,
        )
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(
            [item["role"] for item in detail.json()["messages"]],
            ["user", "assistant", "user", "assistant"],
        )
        self.assertEqual(
            [item["sequence_index"] for item in detail.json()["messages"]],
            [0, 1, 2, 3],
        )

        self.assertEqual(
            self.client.get(
                f"/chat/conversations/{conversation_id}",
                headers=self.bob_headers,
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.delete(
                f"/chat/conversations/{conversation_id}",
                headers=self.bob_headers,
            ).status_code,
            404,
        )

        deleted = self.client.delete(
            f"/chat/conversations/{conversation_id}",
            headers=self.alice_headers,
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(
            self.client.get(
                f"/chat/conversations/{conversation_id}",
                headers=self.alice_headers,
            ).status_code,
            404,
        )

    def test_chat_rejects_conversation_context_switches(self) -> None:
        workspace = self._personal_workspace_id(self.alice_headers)

        with patch(
            "backend.routers.chat.generate_chat_response",
            new=AsyncMock(return_value="Grounded"),
        ) as generate:
            first = self.client.post(
                "/chat/",
                headers=self.alice_headers,
                json={
                    "message": "Workspace question",
                    "workspace_id": workspace,
                    "document_id": None,
                },
            )
            conversation_id = first.json()["conversation_id"]

            alice_id = self._user_id("alice@example.test")
            document = create_document(
                workspace,
                alice_id,
                filename=f"context-{uuid.uuid4().hex}.txt",
            )
            switched = self.client.post(
                "/chat/",
                headers=self.alice_headers,
                json={
                    "message": "Switch context",
                    "workspace_id": workspace,
                    "document_id": document.id,
                    "conversation_id": conversation_id,
                },
            )

        self.assertEqual(switched.status_code, 400)
        self.assertEqual(generate.await_count, 1)

    def test_unauthorized_upload_checks_membership_before_r2_write(self) -> None:
        bob_workspace = self._personal_workspace_id(self.bob_headers)
        with (
            patch(
                "backend.routers.document.read_upload_with_limit",
                new=AsyncMock(return_value=b"text"),
            ) as read_upload,
            patch("backend.routers.document.upload_file", return_value="documents/orphan.txt") as upload,
            patch("backend.routers.document.process_document_logic", new=AsyncMock()),
        ):
            response = self.client.post(
                "/documents/upload",
                headers=self.alice_headers,
                data={"workspace_id": str(bob_workspace), "language": "de"},
                files={"file": ("private.txt", b"text", "text/plain")},
            )
        self.assertEqual(response.status_code, 403)
        read_upload.assert_not_awaited()
        upload.assert_not_called()

    def test_upload_rejects_unsupported_file_type_before_storage(self) -> None:
        with (
            patch("backend.routers.document.upload_file", return_value="documents/file.exe") as upload,
            patch("backend.routers.document.process_document_logic", new=AsyncMock()),
        ):
            response = self.client.post(
                "/documents/upload",
                headers=self.alice_headers,
                files={"file": ("malware.exe", b"MZ", "application/octet-stream")},
            )
        self.assertEqual(response.status_code, 400)
        upload.assert_not_called()

    def test_upload_rejects_oversized_file_before_storage(self) -> None:
        with (
            patch.object(upload_validation, "MAX_UPLOAD_SIZE_BYTES", 5),
            patch("backend.routers.document.upload_file") as upload,
        ):
            response = self.client.post(
                "/documents/upload",
                headers=self.alice_headers,
                files={"file": ("large.txt", b"123456", "text/plain")},
            )

        self.assertEqual(response.status_code, 413)
        upload.assert_not_called()

    def test_upload_rejects_disguised_file_before_storage(self) -> None:
        with patch("backend.routers.document.upload_file") as upload:
            response = self.client.post(
                "/documents/upload",
                headers=self.alice_headers,
                files={"file": ("fake.pdf", b"this is plain text", "application/pdf")},
            )

        self.assertEqual(response.status_code, 400)
        upload.assert_not_called()

    def test_upload_uses_validated_filename_and_content_type(self) -> None:
        with (
            patch(
                "backend.routers.document.upload_file",
                return_value="documents/validated.txt",
            ) as upload,
            patch("backend.routers.document.delete_file") as cleanup,
            patch(
                "backend.routers.document.process_document_logic",
                new=AsyncMock(),
            ),
        ):
            response = self.client.post(
                "/documents/upload",
                headers=self.alice_headers,
                files={"file": ("notes.txt", b"Valid UTF-8 text", "application/octet-stream")},
            )

        self.assertEqual(response.status_code, 200, response.text)
        upload.assert_called_once_with(b"Valid UTF-8 text", "notes.txt")
        cleanup.assert_not_called()

        db = SessionLocal()
        try:
            document = db.query(Document).filter(
                Document.id == response.json()["document_id"]
            ).one()
            self.assertEqual(document.filename, "notes.txt")
            self.assertEqual(document.file_type, "text/plain")
        finally:
            db.close()

    def test_upload_cleans_r2_object_when_database_commit_fails(self) -> None:
        workspace_id = self._personal_workspace_id(self.alice_headers)
        filename = f"commit-failure-{uuid.uuid4().hex}.txt"
        router_db = SessionLocal()

        with (
            patch("backend.routers.document.SessionLocal", return_value=router_db),
            patch.object(router_db, "commit", side_effect=RuntimeError("database unavailable")),
            patch(
                "backend.routers.document.upload_file",
                return_value="documents/orphan.txt",
            ),
            patch("backend.routers.document.delete_file") as cleanup,
        ):
            response = self.client.post(
                "/documents/upload",
                headers=self.alice_headers,
                data={"workspace_id": str(workspace_id)},
                files={"file": (filename, b"Valid UTF-8 text", "text/plain")},
            )

        self.assertEqual(response.status_code, 500)
        cleanup.assert_called_once_with("documents/orphan.txt")

        db = SessionLocal()
        try:
            self.assertIsNone(
                db.query(Document).filter(Document.filename == filename).first()
            )
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
