![InsightAI Logo](frontend/public/logo.png)

![License: MIT](https://img.shields.io/badge/license-MIT-brightgreen) ![Python ≥3.10](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![Node ≥18](https://img.shields.io/badge/node-%3E%3D18-green)

**InsightAI** is a modern web application designed to help users extract insights from their documents efficiently. Users can upload PDFs, CSV files, or connect to API data. The integrated AI analyzes the content, generates professional reports, and answers specific questions about the data (Chat feature in progress).

> **Note:** Currently, the application is fully optimized for **PDF documents**. CSV upload and API-connected data are planned features (in progress).

---

## ⚡ Features

- **Document Upload:** Currently optimized for PDFs. CSV and API-connected data support is in progress.  
- **AI-Powered Analysis:** Automatically generates structured reports and summaries.  
- **Interactive Interface:** View reports, explore sections, and access key metrics.  
- **Quick Insights:** Ask specific questions about your documents (Chat feature in progress).  
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
2. Upload a PDF document via the Upload Zone.  
3. Wait for AI processing (status shown in sidebar).  
4. Click on the document to view the generated report.  
5. Use the chat panel to ask specific questions about the document content (feature in progress).  

CSV and API-connected documents are not fully supported yet and may not generate complete reports.

## Tech Stack
- Frontend: React, TypeScript, Tailwind CSS, Framer Motion
- Backend: Python, FastAPI, Pydantic
- AI: OpenAI API (LLM for report generation)
- Database: SQLite / PostgreSQL (configurable)
- State Management: React Hooks & Context

## Roadmap (Planned Features)
- Full CSV support for document upload and analysis
- API-connected data ingestion
- Chat feature for asking questions about documents
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
