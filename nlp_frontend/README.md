# 🤖 NLP Data Bot - Frontend

This is the user interface for the **NLP Industrial Data Bot**, powered by **Llama 3.1 (8B)**. It is built with a focus on premium aesthetics and responsive data visualization for industrial and MES datasets.

---

## 📦 Requirements (Installation)

Unlike the Backend which uses `requirements.txt`, the Frontend uses the **`package.json`** file to handle all its dependencies and scripts.

### **The "Requirement" file:**
> [!IMPORTANT]
> **File:** [`package.json`](./package.json)  
> This file lists all the libraries (React, Tailwind, Recharts, etc.) that the frontend needs to work. It is the exact equivalent of `requirements.txt` in Python.

---

## 🚀 Getting Started

### **1. Install Dependencies**
To install all the "requirements" listed in `package.json`, run:
```bash
npm install
```

### **2. Run Development Server**
To start the app with Hot Module Replacement (HMR), run:
```bash
npm run dev
```
By default, the app will be available at: `http://localhost:3000` (or as specified in your terminal).

---

## ⚙️ Configuration (Environment Variables)

Before running the application, ensure you have configured the environment variables. 

1.  Create a `.env` file in the `nlp_frontend` directory (copy from `.env.example`).
2.  Set the `VITE_API_URL` to point to your backend (default is `http://127.0.0.1:8000`).

```env
# Example .env content
VITE_API_URL=http://127.0.0.1:8000
VITE_APP_NAME="NLP Industrial Bot"
```

---

## 🛠️ Tech Stack
- **Framework:** [React 19](https://react.dev/)
- **Build Tool:** [Vite](https://vite.dev/)
- **Language:** [TypeScript](https://www.typescriptlang.org/)
- **Styling:** [Tailwind CSS](https://tailwindcss.com/)
- **Icons:** [Lucide React](https://lucide.dev/)
- **Components:** Radix UI / Shadcn UI primitives
- **Charts:** [Recharts](https://recharts.org/) & [Vega-Lite](https://vega.github.io/vega-lite/)

---

## ✨ UI Features
- **Dark Mode First:** Premium high-contrast dark aesthetic.
- **Glassmorphism:** Modern transparent UI elements with blur effects.
- **Dynamic Charts:** Automatically renders data into interactive charts using Vega-Lite and Recharts.
- **Responsive Tables:** Clean, sortable data grids for viewing SQL results.
- **Typo Resilience Feedback:** Shows how the AI interpreted your query in real-time.

---

## 📁 Directory Structure
- `/src/components`: UI building blocks (Buttons, Inputs, etc.)
- `/src/pages`: Main application views (Dashboard, Login, Chat)
- `/src/services`: API connection logic to the Backend
- `/src/hooks`: Custom React logic for state and data fetching
