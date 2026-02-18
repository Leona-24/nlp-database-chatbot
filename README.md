# 🤖 NLP Data Bot - Intelligent SQL Retrieval System

A premium, full-stack application that bridges the gap between natural language and complex database queries. Users can authenticate, connect to various databases (SQLite, PostgreSQL, MySQL), and query their data using plain English.

---

## ✨ Features

### 🔐 Secure Authentication
- **User System**: Complete Sign Up and Login flow.
- **Security**: Industry-standard **Bcrypt** password hashing (72-byte secure limit).
- **Session Management**: Secure **JWT (JSON Web Tokens)** for persistent, stateless authentication.

### 🧠 Intelligent NLP Engine
- **Text-to-SQL**: Translates natural language questions into valid SQL queries.
- **Dual-Layer Architecture**: Uses **Llama 3.3 (70B)** via Groq as primary intelligence with a custom **Smart Heuristic Engine** as a robust fallback.
- **Schema-Agnostic**: Dynamically inspects any connected database (PostgreSQL, MySQL, SQLite) to understand its unique structure without prior training.
- **Typo Tolerance**: Handles slang and spelling mistakes (e.g., "hw many usrs") using fuzzy logic.
- **Explainability**: View the AI's "thought process" and the generated SQL before results are shown.

### 📊 Database Connectivity
- **Multi-DB Support**: Out-of-the-box support for **SQLite**, **PostgreSQL**, and **MySQL**.
- **Live Inspection**: Automatically reads tables, columns, and relationships (Foreign Keys) to build a real-time mental map of your data.
- **Schema Exploration**: Visualize your database tables and columns directly in the UI.

### 🎨 Premium UI/UX
- **Modern Design**: High-end dark mode aesthetic with glassmorphism and smooth transitions.
- **Responsive Tables**: View and export query results easily.
- **Real-time Feedback**: Interactive loading states and toast notifications for a fluid experience.

---

## 🛠️ Architecture

- **Frontend**: [React](https://reactjs.org/) + [TypeScript](https://www.typescriptlang.org/) + [TailwindCSS](https://tailwindcss.com/)
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **Security**: [Bcrypt](https://pypi.org/project/bcrypt/) & [python-jose](https://pypi.org/project/python-jose/)
- **AI Stack**:
  - **Primary**: Llama 3.3 70B (State-of-the-art LLM)
  - **Inference**: [Groq](https://groq.com/) / [OpenAI](https://openai.com/)
  - **Fallback**: Custom Heuristic Engine (Fuzzy matching + Regex logic)
- **DB Layer**: [SQLAlchemy](https://www.sqlalchemy.org/)

---

## 💡 Why These Technologies?

- **FastAPI**: Chosen for its high performance and automatic generation of interactive API documentation (Swagger), making development and testing extremely fast.
- **Llama 3.3 70B**: Provides human-like understanding of complex data requests and nuance, far exceeding standard pattern matching.
- **Smart Heuristics**: Ensures the application remains functional offline or if API limits are reached, providing high reliability.
- **SQLAlchemy**: Acts as a "Database Translator." It allows the app to connect to SQLite, PostgreSQL, and MySQL using the same code, while protecting against SQL Injection attacks.
- **Bcrypt**: The gold standard for password security. It includes a built-in "salt" to prevent rainbow table attacks.
- **TailwindCSS**: Enables us to build a custom, premium UI without writing thousands of lines of CSS, ensuring the app remains lightweight and responsive.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**

### Quick Start (Recommended)
Run the automated startup script in PowerShell:
```powershell
.\start_application.ps1
```

### Manual Installation

#### 1. Backend Setup
```bash
cd nlp_backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend Setup
```bash
cd nlp_frontend
npm install
npm run dev -- --port 3000
```

---

## 📖 Usage Guide

1. **Register/Login**: Start by creating a new account. 
2. **Connect**: Click **"Connect Database"**. Use **"Load Demo Data"** to explore the sample datasets (Students, Customers, Orders).
3. **Query**: Enter a natural language question in the search bar:
   - *"Show all students with GPA > 3.5"*
   - *"How many customers are in Chennai?"*
   - *"hw many usrs are there"* (Typo resilient!)
   - *"Total amount of orders per customer"*
4. **Go Deep**: Explore the **Schema Viewer** to see exactly what the AI has mapped from your database.

---

## 🛡️ Security Notes
- This prototype uses direct Bcrypt hashing. For production use, always use environment variables for the `SECRET_KEY` and database credentials.
- The NLP engine is **Read-Only**: It strictly permits `SELECT` statements, blocking `DROP`, `DELETE`, or `UPDATE` commands at the core level.

---

## ⚡ Extension
The application is designed to be **Zero-Training Required**. You can connect any proprietary database structure, and the AI will immediately utilize its schema-sensing ability to provide answers based on your unique column names and relationships.
