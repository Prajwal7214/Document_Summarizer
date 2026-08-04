# 📄 Summarix

**Summarix** is a production-ready, full-stack AI-powered document summarization and RAG (Retrieval-Augmented Generation) chat application. It features a modern React frontend, a FastAPI backend, Redis caching, Qdrant vector database, Nginx reverse proxy, Docker Compose containerization, Terraform Infrastructure-as-Code (IaC), and automated GitHub Actions CI/CD deployment on AWS EC2.

---

## ✨ Key Features

| Feature | Details |
|---|---|
| 🔐 **Authentication** | Sign up / Log in with persistent sessions (stored in localStorage) |
| 👤 **User Profile** | Sidebar profile section with avatar initials, name, email, and logout |
| 📄 **Single Document Summary** | Upload one PDF, DOCX, or TXT → get a structured AI summary |
| 📚 **Multi-Document Summary** | Upload up to 10 files simultaneously → compare in a results table |
| 🧠 **Three Summary Modes** | Short (3 bullets), Detailed (full paragraph), Academic (formal abstract) |
| 💬 **RAG Document Chat** | Ask questions about your document using Qdrant vector search + AI |
| ⬇️ **Export Summaries** | Download single summaries as **PDF**; multi-doc results as **CSV** or **PDF table** |
| ⚡ **Smart Redis Caching** | Previously generated summaries are instantly retrieved from Redis cache |
| 🔄 **AI Fallback Chain** | Gemini → Groq → Ollama (automatic, no manual switching needed) |
| 🌐 **Nginx Reverse Proxy** | Port 80 same-origin routing for zero CORS issues and no hardcoded IPs |
| ☁️ **Infrastructure as Code** | Terraform scripts for automated AWS VPC, EC2, Elastic IP, and SG provisioning |
| 🚀 **Automated CI/CD** | GitHub Actions pipeline for auto-deploying updates to AWS EC2 |

---

## 🏗️ System Architecture

```mermaid
graph TD
    Client[Browser / User on Port 80] -->|HTTP / HTTPS| Nginx[Frontend Container: Nginx Port 80]
    Nginx -->|Serves Static Build| SPA[React 19 SPA Bundle]
    Nginx -->|Proxy Pass /api/| Backend[FastAPI Backend Container Port 8000]
    Backend -->|Cache Query| Redis[Redis Container Port 6379]
    Backend -->|Vector Search| Qdrant[Qdrant Container Port 6333]
    Backend -->|LLM Inference| AI[Google Gemini / Groq / Ollama]
```

---

## 🚀 Tech Stack

### Frontend & Web Server
- **React 19** + **Vite 8** + **TypeScript**
- **Tailwind CSS v4** — utility-first styling
- **Nginx (Alpine)** — production static file web server & API reverse proxy
- **React Router v7** — client-side routing with protected routes
- **Lucide React** — icon library

### Backend & AI Infrastructure
- **Python 3.10+** + **FastAPI** (v0.115) + **Uvicorn**
- **Google Gemini** (`gemini-2.0-flash`) — primary AI model
- **Groq** — secondary AI fallback
- **Ollama** (`llama3.2`) — local AI fallback (offline capability)
- **Qdrant** — vector database for RAG document embeddings
- **Redis 7** — high-performance summary caching
- **ReportLab** — server-side PDF export generation
- **PyPDF + python-docx** — multi-format document parsing

### DevOps & Cloud Infrastructure
- **AWS EC2** — `t3.micro` instance (Amazon Linux 2023)
- **AWS Elastic IP (EIP)** — static IP allocation
- **Terraform** — VPC, Subnet, Internet Gateway, Security Groups, EC2, EIP
- **Docker & Docker Compose** — multi-container orchestration
- **GitHub Actions** — automated CI/CD deployment pipeline

---

## 📁 Project Structure

```text
document_summarizer/
├── .github/
│   └── workflows/
│       └── deploy.yml              # GitHub Actions CI/CD pipeline
│
├── DevOps/
│   └── Terraform/                  # Infrastructure as Code (IaC)
│       ├── provider.tf             # AWS provider configuration
│       ├── vpc.tf                  # Custom VPC definition
│       ├── subnet.tf               # Public subnet
│       ├── internet_gateway.tf     # Internet Gateway
│       ├── route_table.tf          # Route table & subnet association
│       ├── security_group.tf       # Security group (Ports 22, 80)
│       ├── ec2.tf                  # EC2 instance (30GB gp3 volume)
│       ├── elastic_ip.tf           # Static Elastic IP allocation
│       ├── variables.tf            # Input variables
│       ├── outputs.tf              # Outputs (Public IP, DNS, EIP)
│       ├── terraform.tfvars        # Variable definitions
│       └── user_data.sh            # EC2 bootstrap initialization script
│
├── backend/                        # FastAPI backend
│   ├── main.py                     # App entry point, CORS, upload limits
│   ├── config.py                   # Settings & environment variables
│   ├── requirements.txt            # Python dependencies (CPU-optimized PyTorch)
│   ├── Dockerfile                  # Backend container configuration
│   ├── routers/                    # API routes (/summarize, /download, /chat)
│   ├── services/                   # AI client, RAG, cache, parsers, export generators
│   └── models/                     # Pydantic schemas
│
├── frontend/                       # React frontend
│   ├── src/                        # React components, pages, context, styles
│   ├── nginx.conf                  # Production Nginx reverse proxy configuration
│   ├── Dockerfile                  # Multi-stage Dockerfile (build & Nginx stage)
│   ├── package.json                # Frontend dependencies & build script
│   └── vite.config.ts              # Vite configuration
│
├── docker-compose.yml              # Docker Compose multi-container configuration
└── DEPLOYMENT_DEBUGGING_REPORT.md  # Comprehensive deployment case study
```

---

## 🐳 Running with Docker Compose (Recommended)

To run the entire application stack locally or on a server using Docker:

### 1. Prerequisites
- **Docker** & **Docker Compose** installed.

### 2. Environment Setup
Create a `.env` file in the `backend/` directory:

```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
CORS_ORIGINS=*
```

### 3. Build & Launch Containers

```bash
# Clone the repository
git clone https://github.com/Prajwal7214/Document_Summarizer.git
cd Document_Summarizer

# Start all services in detached mode
docker compose up --build -d

# Verify container status
docker compose ps
```

The application will be accessible at:
- **Web App**: `http://localhost` (Port 80)
- **Backend API Docs**: `http://localhost:8000/docs`

---

## ☁️ Infrastructure Deployment with Terraform

Provision AWS EC2, VPC, Security Groups, and Elastic IP automatically using Terraform:

### 1. Prerequisites
- **Terraform CLI** (v1.5+)
- **AWS CLI** configured with credentials (`aws configure`)

### 2. Deploy Infrastructure

```bash
cd Devops/Terraform

# Initialize Terraform modules
terraform init

# Validate configuration
terraform validate

# Review execution plan
terraform plan

# Apply infrastructure changes
terraform apply -auto-approve
```

Upon completion, Terraform will output your EC2 **Public IP** and **Elastic IP**.

---

## 🔄 CI/CD Automated Deployment

Automated deployment is configured via GitHub Actions (`.github/workflows/deploy.yml`).

### Setup GitHub Secrets
In your GitHub repository under **Settings > Secrets and variables > Actions**, add:

- `EC2_HOST`: Your AWS EC2 Public IP or Elastic IP
- `EC2_USER`: `ec2-user`
- `EC2_SSH_KEY`: Contents of your private SSH key (`.pem`)
- `PROJECT_PATH`: `/home/ec2-user/Document_Summarizer`

Pushing to the deployment branch triggers automatic `git pull`, container rebuild, and deployment cleanup.

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check |
| `POST` | `/api/v1/summarize` | Summarize a single document |
| `POST` | `/api/v1/summarize-multiple` | Summarize up to 10 documents |
| `POST` | `/api/v1/download/pdf` | Export single summary as PDF |
| `POST` | `/api/v1/download/csv` | Export multi-doc results as CSV |
| `POST` | `/api/v1/download/table-pdf` | Export multi-doc results as PDF table |
| `POST` | `/api/v1/chat/ingest` | Ingest a document into Qdrant vector store |
| `POST` | `/api/v1/chat/ask` | Ask a question about an ingested document |
| `GET` | `/api/v1/chat/documents` | List all ingested documents |
| `DELETE` | `/api/v1/chat/documents/{id}` | Remove document from vector store |
| `GET` | `/cache/stats` | View Redis cache statistics |
| `DELETE` | `/cache/clear` | Clear summary cache |

---

## 📝 Supported File Types

| Format | Extension | Max Size |
|---|---|---|
| PDF | `.pdf` | 10 MB |
| Word Document | `.docx` | 10 MB |
| Plain Text | `.txt` | 10 MB |

> Maximum **10 files** per multi-document request (100 MB total limit).

---

## 🤖 AI Model Fallback Chain

The backend automatically attempts models in order of priority:

```
Google Gemini (gemini-2.0-flash)
        ↓ (if rate-limited / unavailable)
Groq (Fast Cloud Inference)
        ↓ (if unavailable)
Ollama (llama3.2 — Local / Offline)
```

---

*Built with React + FastAPI + Nginx + Redis + Qdrant + Terraform + AWS EC2 + GitHub Actions*
