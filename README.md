# Chatbot Backend API

This backend provides user authentication, document upload, chatbot creation, and management endpoints. All endpoints (except registration and login) require a valid JWT Bearer token.

## Authentication

### Register User
**POST** `/users/register`
Register a new user.
**Body:**
```json
{
  "email": "user@example.com",
  "password": "yourpassword",
  "confirm_password": "yourpassword"
}
```

### Login For Access Token
**POST** `/users/login`
Obtain a JWT access token.
**Body:**
```json
{
  "username": "user@example.com",
  "password": "yourpassword"
}
```
**Response:**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer"
}
```

### Read Users Me
**GET** `/users/auth/me`
Get current user info.
**Headers:**
`Authorization: Bearer <access_token>`

### Update User Profile
**PUT** `/users/profile`
Update user profile fields.
**Body:**
```json
{
  "name": "New Name",
  "bio": "About me"
}
```

---

## Chatbots & Documents

### Upload Pdf
**POST** `/chatbots/upload`
Upload one or more PDF files.
**Form Data:**
- `files`: List of PDF files

### Get Documents
**GET** `/chatbots/documents`
List all documents uploaded by the current user.

### Chat With Document
**POST** `/chatbots/chat_with_document`
Query a document collection and get an AI-generated response.
**Body:**
```json
{
  "query": "What is the summary?",
  "collection_name": "my_collection"
}
```

### List Collections
**GET** `/chatbots/list_collections`
List all ChromaDB collection names.

### Create Chatbot
**POST** `/chatbots/create_chatbot`
Create a new chatbot and associate documents.
**Form Data:**
- `name`: string
- `systemPrompt`: string
- `welcomeMessage`: string
- `theme`: string
- `primaryColor`: string
- `selectedDocuments`: array of document IDs
- `newDocument`: array of PDF files (optional)

### Get Chatbots
**GET** `/chatbots/get_chatbots`
List all chatbots for the current user.

### Add Documents To Chatbot
**POST** `/chatbots/chatbot/{chatbot_id}/add_documents`
Add new or existing documents to a chatbot.
**Path:**
- `chatbot_id`: string
**Form Data:**
- `new_documents`: array of PDF files (optional)
- `existing_document_ids`: array of document IDs

### Update Chatbot
**PUT** `/chatbots/chatbot/{chatbot_id}/update`
Update chatbot configuration and associated documents.
**Path:**
- `chatbot_id`: string
**Form Data:**
- `name`, `systemPrompt`, `welcomeMessage`, `theme`, `primaryColor`: (all optional)
- `selectedDocuments`: array of document IDs

---

## Utilities

### Reset Database
**DELETE** `/reset`
Drop and recreate all tables (development only).

### Check Health
**GET** `/`
Health check endpoint.

---

## Authentication

All protected endpoints require the `Authorization: Bearer <access_token>` header.

---

## Error Handling

- 401 Unauthorized: Invalid or expired token.
- 404 Not Found: Resource does not exist or access denied.
- 400 Bad Request: Invalid input or file type.

---

## Example Usage

**Register:**
```bash
curl -X POST http://localhost:8000/users/register -H "Content-Type: application/json" -d '{"email":"user@example.com","password":"pass","confirm_password":"pass"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/users/login -H "Content-Type: application/json" -d '{"username":"user@example.com","password":"pass"}'
```

**Upload PDF:**
```bash
curl -X POST http://localhost:8000/chatbots/upload -H "Authorization: Bearer <token>" -F "files=@/path/to/file.pdf"
```

---

For more details, see the OpenAPI docs at `/docs` or `/redoc` when running the server.
