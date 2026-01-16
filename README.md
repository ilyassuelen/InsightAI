![InsightAI Logo](frontend/public/logo.png)

![License: MIT](https://img.shields.io/badge/license-MIT-brightgreen) ![Python ≥3.10](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![Node ≥18](https://img.shields.io/badge/node-%3E%3D18-green)

**InsightAI** is a modern web application designed to help users extract insights from their documents efficiently. Users can upload PDFs, CSVs, DOCX, TXT-files or connect to API data. The integrated AI analyzes the content, generates professional reports, and now includes the **first version of a document-aware chat feature**.

> **Note:** Currently, the application is fully optimized for **PDF, CSV, DOCX and TXT documents**. API-connected data is a planned feature.

---

## ⚡ Features

- **Document Upload:** Supports PDFs, CSVs, DOCXs and TXTs. 
- **AI-Powered Analysis:** Automatically generates structured reports, summaries, and insights using OpenAI LLMs.  
- **Interactive Chat:** Ask questions about your documents directly in the chat (first version now available).
- **Responsive UI:** Optimized for desktop and mobile devices.  

---

## 🛠 Installation

### Prerequisites

- Node.js >= 18  
- Python >= 3.10  
- Git  

### Quick Start (macOS / Linux / Windows PowerShell)

```bash
# Clone the repository
git clone https://github.com/ilyassuelen/InsightAI
cd InsightAI

# Backend setup
cd backend
python -m venv .venv

# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn main:app --reload

# Frontend setup
cd ../frontend
npm install
npm start
```

## ⚙️ Configuration

The app uses environment variables for configuration. Create a `.env` file in the **project root**:

| Name             | Required | Description                                      |
| ---------------- | -------- | ------------------------------------------------ |
| OPENAI_API_KEY   | ✅       | OpenAI API key for AI report generation         |
| DATABASE_URL     | ❌       | Optional DB URL for PostgreSQL (defaults to SQLite) |


## Usage

1. Open the frontend in your browser at [http://localhost:8080](http://localhost:8080).  
2. Upload a Document via the Upload Zone.  
3. Wait for AI processing (status shown in sidebar).  
4. Click on the document to view the generated report.  
5. Use the chat panel to ask specific questions about the document content (first version available).  

(API-connected documents are not supported yet)

## Tech Stack
- Frontend: React, TypeScript, Tailwind CSS, Framer Motion
- Backend: Python, FastAPI, Pydantic
- AI: OpenAI API (LLM for report generation and chat)
- Database: SQLite / PostgreSQL (configurable)
- State Management: React Hooks & Context

## Roadmap (Planned Features)
- Enhanced CSV support for very large files
- API-connected data ingestion
- Enhanced reporting options and visualizations

## 🤝 Contributing
Contributions are welcome! Please follow these steps:
1.	Fork the repository.
2. Create a feature branch: git checkout -b feature/my-feature
3.	Commit your changes: git commit -m 'Add some feature'
4.	Push to the branch: git push origin feature/my-feature
5.	Open a Pull Request

## License
This project is licensed under the [MIT License](./LICENSE).
