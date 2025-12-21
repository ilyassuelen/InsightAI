# Planned API Endpoints – InsightAI

| Endpoint             | Method | Purpose                           | Input                                  | Output                             |
|----------------------|--------|-----------------------------------|----------------------------------------|------------------------------------|
| `/auth/register`     | POST   | Register a new user               | `username`, `email`, `password`        | `success`, `message`               |
| `/auth/login`        | POST   | Log in a user                     | `email`, `password`                    | `token`, `success`, `message`      |
| `/documents/upload`  | POST   | Upload a document                 | File (`CSV`, `JSON`, `PDF`), `user_id` | `document_id`, `status`, `message` |
| `/documents`         | GET    | Get all documents of a user       | `user_id`                              | List all documents                 |
| `/documents/{id}`    | GET    | Get a single document             | `document_id`                          | Document metadata + link/path      |
| `/reports/generate`  | POST   | Generate a report from a document | `document_id`, `report_options`        | `report_id`, `content`, `status`   |
| `/reports/{id}`      | GET    | Retrieve a report                 | `report_id`                            | `content`, `metadata`              |
| `/chat/message`      | POST   | Send a message to the AI agent    | `session_id`, `message`, `user_id`     | `AI_response`, `message_id`        |
| `/chat/{session_id}` | GET    | Get all messages in a session     | `session_id`                           | List of messages                   |
| `/sessions`          | GET    | Get all sessions of a user        | `user_id`                              | List of sessions                   |
| `/sessions`          | POST   | Create a new session              | `user_id`, `session_name`              | `session_id`, `created_at`         |
| `/users/{id}`        | GET    | Retrieve user details             | `user_id`                              | `username`, `email`, `created_at`  |
| `/users/{id}`        | PATCH  | Update user details               | `user_id`, fields to update            | `success`, `message`               |