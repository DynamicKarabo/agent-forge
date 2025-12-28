<<<<<<< HEAD
# agent-forge
Agent workflow platform
=======
# AgentForge

![AgentForge Banner](https://img.shields.io/badge/AgentForge-Build_Autonomous_Workflows-6366f1?style=for-the-badge&logo=openai&logoColor=white)

**AgentForge** is a professional visual builder for orchestrating autonomous AI agent workflows. It enables users to design, connect, and execute multi-agent systems via a drag-and-drop interface, powered by Groq's high-speed inference.

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571.svg?logo=fastapi)
![TailwindCSS](https://img.shields.io/badge/Tailwind-38B2AC.svg?logo=tailwind-css&logoColor=white)

---

## 🚀 Features

- **Visual Workflow Builder**: Intuitive drag-and-drop canvas powered by `jsPlumb` for connecting agents.
- **Specialized Agents**:
  - 🔍 **Researcher**: Fetches real-time data using DuckDuckGo.
  - ✍️ **Writer**: Synthesizes information into professional reports.
  - 🧐 **Critic**: Reviews content for accuracy and tone.
  - 💻 **Coder**: Generates clean, production-ready code.
- **Real-Time Streaming**: Watch agents think and act with live SSE (Server-Sent Events) logs.
- **Tool Calling**: Agents autonomously use tools like `web_search` and `local_rag`.
- **Workflow Persistence**: Save your graphs to JSON and load them back instantly.
- **Demo Mode**: Includes a pre-built "Market Analysis" workflow to get you started.

## 🛠️ Tech Stack

- **Backend**: FastAPI, AsyncGroq, Pydantic, Uvicorn
- **Frontend**: Vanilla HTML5, Alpine.js, Tailwind CSS (CDN-based, no build step required)
- **AI/LLM**: Groq API (Llama3-70b-8192)
- **Tools**: DuckDuckGo Search, ChromaDB, Sentence-Transformers

## 📦 Quick Start

### Prerequisites
- Docker & Docker Compose
- [Groq API Key](https://console.groq.com/)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-portfolio/agentforge.git
   cd agentforge
   ```

2. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=gsk_your_key_here
   ```

3. **Run with Docker**:
   ```bash
   docker-compose up --build
   ```

4. **Access the App**:
   Open **[http://localhost:8000/frontend/index.html](http://localhost:8000/frontend/index.html)** in your browser.
   _(Or simply open `agentforge/frontend/index.html` directly if running locally)_

## 📖 Usage Guide

1. **Build**: Drag agents from the palette onto the canvas.
2. **Connect**: Draw lines between agents to define the execution flow.
3. **Configure**: Click any agent to edit its system prompt.
4. **Execute**: Type a global task (e.g., "Research AI trends") and hit **Run**.
5. **Report**: Once finished, click **Download Report** to get a Markdown summary.

---

## 🖼️ Screenshots

### Canvas
*Drag-and-drop interface for building complex workflows.*

### Live Logs
*Real-time execution feedback with agent-specific coloring.*

---

## ☁️ Deployment

**AgentForge** is designed to be easily deployable.

### Docker
The included `Dockerfile` is production-ready.

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Render / Fly.io
Simply connect your repository and set the `GROQ_API_KEY` environment variable. The app listens on port `8000`.

---

**built with ❤️ by You**
>>>>>>> b5c3553 (Initial Release v1.0)
