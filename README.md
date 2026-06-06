<div align="center">
  <img src="docs/assets/evidra_logo.png" width="150" alt="Evidra Logo" />
  <br/>
  <br/>
  <a href="https://skillicons.dev">
    <img src="https://skillicons.dev/icons?i=fastapi,postgres,python,tailwind&theme=dark" />
  </a>
  <br/>
  <h1>EVIDRA CORE</h1>
  <p><b>Cognitive Talent Intelligence Platform</b></p>
  <h3><i>Find candidates stronger than their resume suggests.</i></h3>
</div>

<br/>

Evidra is an enterprise-grade, AI-driven talent acquisition engine designed to transcend traditional resume parsing. A Cognitive Talent Intelligence Platform that discovers evidence-backed capabilities traditional keyword-based hiring systems miss. By combining deep semantic search, automated GitHub repository auditing, and zero-bias blind evaluation modes, Evidra synthesizes unstructured applicant data into highly actionable, verifiable hiring signals.

Evidra operates on the philosophy of **"Show, Don't Tell"**—moving past inflated resume jargon in favor of evidence-backed technical signals (such as open-source contributions and algorithmic consistency).

---

## ❓ Why Evidra?

Traditional ATS systems evaluate what candidates *claim*. 
Evidra evaluates what candidates *demonstrate*.

By combining semantic understanding, repository intelligence, and explainable reasoning, Evidra helps recruiters identify high-potential candidates that keyword matching alone would miss.

## 🚀 The Evidra Advantage

- **Cognitive Extraction Pipeline**: Utilizes Groq-powered LLMs to ingest chaotic PDF/DOCX resumes and normalize them into structured competency matrices.
- **Deep Semantic Vector Search**: Powered by `pgvector`, allowing recruiters to search via *intent* (e.g. "expert in scalable cloud infrastructure") rather than relying on exact keyword matching.
- **Automated Open-Source Auditing**: Instantly hooks into the GitHub API to calculate code consistency and original repository ratios.
- **Dynamic Reasoning Chamber**: A glassmorphic, real-time interface with built-in auto-polling, providing recruiters with live telemetry of the ingestion pipeline.
- **Anti-Bias Engine**: One-click "Blind Review" mode redacts personally identifiable information (PII) to enforce meritocratic evaluation.

---

## 🎬 Demo Flow

1. **Upload Resume**: Submit a chaotic PDF or DOCX file.
2. **Resume Parsed**: Cognitive extraction structures the data instantly.
3. **GitHub Enrichment**: Background workers analyze public repository activity to identify evidence-backed technical signals.
4. **Hidden Strength Discovery**: Surfacing evidence-backed capabilities that are underrepresented in the candidate's resume.
5. **Explainability Generation**: AI generates an explainable recommendation narrative grounded in the candidate's available evidence.
6. **Semantic Search**: Use natural language to query the entire vector database.
7. **Candidate Recommendation**: Dynamic ranking adjustments based on the selected hiring persona.

---

## 🎥 Live Demo

![Demo](docs/assets/evidra-demo.gif)

*Watch Evidra ingest a chaotic resume, discover hidden strengths, execute a semantic search, and dynamically surface the top-recommended candidate in real-time.*

---

## 📊 Sample Outcome

**Candidate:** Arjun

**Resume Claim:**
> Backend Development

**Evidence Detected:**
> ESP32 Networking, Distributed Systems, IoT Architecture

**Hidden Strength:**
> Systems Thinking

**Recommendation:**
> Top Recommended

---

## 💼 Business Impact

Evidra helps technical recruiters and engineering managers:
- **Reduce reliance on keyword matching** and boolean search strings.
- **Surface overlooked technical talent** hidden behind poorly formatted resumes.
- **Improve explainability in hiring decisions** with detailed narrative trails.
- **Introduce bias-reduction workflows** through an engineered blind-review process.
- **Make evidence-backed hiring recommendations** grounded in code, not claims.

---

## ⚡ Platform Capabilities

- **384-dimensional semantic embeddings** for intent-based search.
- **Multi-tenant architecture** supporting distinct organizations and jobs.
- **Real-time candidate enrichment pipeline** with ultra-fast asynchronous polling.
- **Blind-review evaluation mode** for immediate PII obfuscation.
- **Explainable recommendation engine** powered by Groq and Llama-3.
- **Vector-powered natural language search** leveraging PostgreSQL and `pgvector`.

---

## 🖼 System Interface & Visuals

*(Note: Replace placeholders with actual implementation screenshots before final submission)*

### 1. Central Command Dashboard
![Dashboard Placeholder](docs/assets/dashboard.png)
*Real-time overview of the candidate pipeline, auto-polling metrics, and live signal feed.*

### 2. Discovery Event
![Discovery Event Placeholder](docs/assets/discovery_event.png)
*Real-time signal extraction identifying a hidden strength directly from GitHub audit telemetry.*

### 3. Reasoning Chamber & Explainability
![Reasoning Chamber Placeholder](docs/assets/reasoning.png)
*The AI analyst narrative detailing why a candidate was shortlisted, referencing specific evidence.*

### 3. Blind Review Mode
![Blind Review Placeholder](docs/assets/blind_review.png)
*PII obfuscation dynamically rendering names, gender, and contact info invisible to enforce zero-bias evaluation.*

### 4. Competency Graph Visualization
![Competency Graph Placeholder](docs/assets/graph.png)
*Interactive node-map isolating verified skills vs. claimed skills and discovered hidden strengths.*

---

## 🧠 System Architecture

Evidra's architecture is decoupled, scalable, and built for real-time inference. The ingestion pipeline offloads heavy cognitive tasks to background threads, ensuring the recruiter dashboard remains hyper-responsive.

```mermaid
graph TD
    %% Define Styles
    classDef client fill:#0f172a,stroke:#6366f1,stroke-width:2px,color:#fff;
    classDef api fill:#1e1e2f,stroke:#8b5cf6,stroke-width:2px,color:#fff;
    classDef worker fill:#1e1e2f,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef db fill:#001a33,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef external fill:#111,stroke:#f59e0b,stroke-width:1px,color:#aaa,stroke-dasharray: 5 5;

    %% Nodes
    UI([Evidra Client Dashboard]):::client
    API[FastAPI Core Router]:::api
    
    DB[(PostgreSQL + pgvector)]:::db
    
    Extract[Cognitive Resume Extractor]:::worker
    Embed[Semantic Embedder]:::worker
    Git[GitHub Enrichment Engine]:::worker
    Rank[Dynamic Scoring Engine]:::worker

    Groq[Groq Llama-3 API]:::external
    GitHub[GitHub GraphQL]:::external

    %% Flow
    UI -->|1. Upload PDF| API
    UI -->|5. Real-time Polling| API
    UI -->|Deep Search Query| API
    
    API -->|2. Async Dispatch| Extract
    Extract -->|Calls| Groq
    Extract -->|Parsed JSON| DB
    
    API -->|3. Background Task| Git
    Git -->|Audit| GitHub
    Git -->|Updates| DB
    
    API -->|4. Generate Vector| Embed
    Embed -->|Store 384d Vector| DB
    
    API -->|Rerank Candidates| Rank
    Rank -->|Fetch Context| DB
    Rank -->|Weights| UI
```

---

## 🛠 Technology Stack

### **Frontend Interface (The Command Center)**
* **Core:** Vanilla JS (ES6+), HTML5 Canvas for dynamic node graphs
* **Styling:** TailwindCSS 3.x (compiled via CDN)
* **Architecture:** State-driven reactive rendering pattern
* **Aesthetics:** Midnight theme, glassmorphism UI, SVG data visualization

### **Backend Core (The Intelligence Engine)**
* **Framework:** FastAPI (Python 3.10+)
* **Concurrency:** `asyncio` & `httpx` for ultra-fast non-blocking API calls
* **Database Layer:** SQLModel / SQLAlchemy
* **Vector Store:** PostgreSQL extended with `pgvector` for `<=>` cosine similarity operations
* **Background Workers:** FastAPI `BackgroundTasks` for seamless off-cycle enrichment

### **AI & Third-Party Services**
* **LLM Provider:** Groq Engine (for near-instant zero-shot extraction)
* **API Providers:** GitHub REST/GraphQL APIs
* **Security:** JWT-based stateless authentication

---

## 🧮 How the AI Scoring Model Works

The scoring engine combines multiple evidence dimensions into a composite recommendation signal. Candidates are categorized into:
- **Top Recommended**
- **Recommended**
- **Review Required**

Thresholds are configurable based on organizational hiring preferences. The final score is synthesized from four primary dimensions:

1. **Verified Skills Coverage**: Ratio of skills claimed vs. skills mathematically verified by the platform.
2. **Growth Trajectory**: Open-source activity contributes additional evidence signals when available.
3. **Hidden Strengths Bonus**: Hidden Strengths are surfaced only when corroborated by repository evidence and behavioral signals.
4. **Role Persona Fit**: Contextual evaluation against the current active persona (e.g. `startup_generalist` vs `enterprise_specialist`).

---

## 🔭 Future Roadmap

- **LinkedIn Enrichment**: Automated syncing of professional network signals.
- **ATS Integrations**: Push/pull integrations with Workday, Lever, and Greenhouse.
- **Multi-Model Explainability**: Toggle between Groq Llama-3, GPT-4, and Claude for reasoning.
- **Enterprise SSO**: SAML/OAuth integration for enterprise deployment.
- **Team Collaboration Workspaces**: Shared candidate pipelines with collaborative scoring.

---

## 💻 Getting Started (Local Development)

### 1. Database Setup
Evidra requires PostgreSQL with the `pgvector` extension installed.
```bash
# Using Docker
docker run -d -e POSTGRES_USER=evidra -e POSTGRES_PASSWORD=evidra -e POSTGRES_DB=evidra -p 5432:5432 ankane/pgvector
```

### 2. Backend Initialization
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt

# Configure Environment
echo "DATABASE_URL=postgresql+asyncpg://evidra:evidra@localhost:5432/evidra" > .env
echo "GROQ_API_KEY=your_groq_key" >> .env
echo "GITHUB_TOKEN=your_github_pat" >> .env

# Run Migrations & Boot
python main.py
```

### 3. Frontend Deployment
The frontend is completely decoupled. Simply serve the `frontend` directory using any static web server:
```bash
cd frontend
python -m http.server 8000
```
Then navigate to `http://localhost:8000` in your browser.

---

## 🔒 Security & Privacy Notice
All candidate resumes parsed by the system remain strictly within the designated PostgreSQL tenant. External API calls (like GitHub parsing) strip PII prior to transmission. The "Blind Review" mode ensures all personally identifiable traits are masked at the presentation layer during the critical shortlist phase.

---
<div align="center">
  <i>Evidra — Truth in Talent. Engineered for the Next Generation of Technical Recruitment.</i>
</div>
