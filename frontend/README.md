# 🎨 Summarix Frontend

This is the frontend application for **Summarix**, a modern, AI-powered document summarization tool.

It is built to interface directly with the Summarix FastAPI backend, providing users with a beautiful, responsive, and intuitive UI to upload documents, generate summaries, and chat with their files.

---

## 🚀 Tech Stack
- **Framework:** React 18
- **Build Tool:** Vite
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Routing:** React Router v6
- **Icons:** Lucide React

---

## 📁 Folder Structure

- `src/components/`: Reusable UI components (`FileUpload`, `Layout`, `ResultsTable`)
- `src/pages/`: Main application views (`Home`, `Summary`, `Documents`, `Chat`)
- `src/contexts/`: Global state management (`ToastContext` for notification alerts)

---

## 🔧 Setup Instructions

1. Ensure you have **Node.js** installed.
2. Navigate to this directory in your terminal:
   ```bash
   cd frontend
   ```
3. Install the dependencies:
   ```bash
   npm install
   ```
4. Start the development server:
   ```bash
   npm run dev
   ```
5. Open your browser to `http://localhost:5173`.

> **⚠️ Note:** The frontend expects the Summarix backend to be running simultaneously on `http://localhost:8000` for all API requests to succeed. Make sure your FastAPI backend is running!
