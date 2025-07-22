# AI-Powered DevOps Co-Pilot for Large-Scale Server Maintenance

This project showcases a sophisticated, multi-faceted system that combines Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), and direct CI/CD integration to create a powerful AI Co-Pilot for DevOps and SRE teams. The system is designed to intelligently manage and maintain a fleet of up to 2000 servers, demonstrating a modern approach to automating platform engineering tasks.

## Core Components

The repository is divided into two main projects that work in concert:

1.  **LangChain/LangGraph Maintenance Orchestrator (Python):** A powerful AI agent that acts as the "brain" of the operation. It uses a multi-agent architecture to diagnose server issues, propose solutions, and generate maintenance scripts.
2.  **Jenkins MCP Server (TypeScript):** A secure bridge that exposes Jenkins functionalities as tools for the AI agent, enabling it to perform real-world actions like running Ansible playbooks and managing build jobs.

---

## System Architecture

This diagram illustrates the end-to-end workflow, from user interaction to task execution on the server fleet.

```ascii
+------------------+      +---------------------------------+      +--------------------------+
|   DevOps / SRE   |----->|   AI Maintenance Orchestrator   |----->|   Jenkins MCP Server     |
|      (User)      |      |         (Python / LangChain)    |      |      (TypeScript)        |
+------------------+      +---------------------------------+      +--------------------------+
                            |         ^               ^   |              |
                            |         |               |   |              | MCP Tool Call
                            | RAG     | Human         |   |              | (Run Ansible, etc.)
                            | Query   | Approval      |   |              V
                            V         |               |   |      +--------------------------+
+------------------+      +------------------+      +------------------+      |      Jenkins API         |
|  ChromaDB        |<-----|  LangGraph Agent |      |  OpenAI LLM      |      |                          |
| (Vector Store)   |      |   (Supervisor)   |----->| (Reasoning)      |      +--------------------------+
+------------------+      +------------------+      +------------------+              |
                            |         ^                                              |
                            |         |                                              V
                            V         |                                     +-------------------+
+------------------+      +------------------+      +------------------+    |   Server Fleet    |
|  Log Analysis    |<-----| Solution Agent   |----->|  Doc Agent       |    | (2000 Servers)    |
|      Agent       |      |                  |      | (Chronicle)      |    +-------------------+
+------------------+      +------------------+      +------------------+

```

---

## 1. AI Maintenance Orchestrator (Python)

This is the primary application, built with LangChain and the latest LangGraph framework. It simulates a real-world scenario where an AI assistant helps a Platform Engineer manage a large and complex server infrastructure.

### Key Features

-   **Multi-Agent Architecture:** Utilizes a supervisor-agent pattern where a primary supervisor coordinates specialized agents for log analysis, solution generation, and documentation.
-   **Retrieval-Augmented Generation (RAG):** Ingests and processes server-related documents (logs, issue reports, solution manuals) into a Chroma vector database for context-aware analysis.
-   **Cross-Server Intelligence:** Maintains a global knowledge base to correlate issues across the entire server fleet, enabling it to identify trends and suggest solutions based on historical data from all servers.
-   **Dynamic & Scalable:** Designed to dynamically register and manage servers, scaling from a handful to thousands.
-   **Human-in-the-Loop:** Incorporates critical human approval steps before executing potentially risky actions, ensuring safety and oversight.
-   **Automated Scripting:** Generates production-ready `bash` maintenance scripts and comprehensive rollback plans based on its analysis.
-   **Comprehensive Auditing:** Creates a detailed "chronicle" of each maintenance session for reporting and auditing purposes.

### Tech Stack

-   **Python 3.10+**
-   **LangChain & LangGraph:** For building the core agentic workflow and multi-agent orchestration.
-   **OpenAI:** As the LLM for reasoning, analysis, and generation.
-   **ChromaDB:** As the vector store for the RAG pipeline.
-   **PyPDF, Pandas:** For document loading and data manipulation.

### How to Run

1.  **Set up the environment:**
    ```bash
    python -m venv langchain-env
    source langchain-env/bin/activate
    pip install -r requirements.txt
    ```

2.  **Configure your API Key:**
    -   Create a `.env` file in the root directory.
    -   Add your OpenAI API key: `OPENAI_API_KEY="your-key-here"`

3.  **Run the demonstration scenarios:**
    The `scenarios.py` file contains a suite of demonstrations that showcase the system's capabilities without requiring real server data.
    ```bash
    python scenarios.py
    ```

---

## 2. Jenkins MCP Server (TypeScript)

This component is a Node.js server that implements the **Model Context Protocol (MCP)**. It acts as a secure API layer that translates AI tool calls into actual Jenkins API requests. This allows the Python-based LangChain agent to safely and effectively delegate tasks to a Jenkins CI/CD server.

### Key Features

-   **Secure Tool Exposure:** Safely exposes Jenkins actions like triggering builds, running Ansible ad-hoc commands, and checking job statuses.
-   **Safety First:** Includes robust validation for commands, Ansible modules, and inventory to prevent dangerous operations.
-   **Asynchronous Job Handling:** Intelligently polls Jenkins for the status of long-running jobs and handles timeouts gracefully.
-   **Environment-Driven Configuration:** Fully configurable via environment variables for easy deployment.
-   **Model Context Protocol:** Implements a modern standard for AI-to-tool communication.

### Tech Stack

-   **TypeScript / Node.js**
-   **@modelcontextprotocol/sdk:** The official SDK for building MCP-compliant servers.
-   **Axios:** For making HTTP requests to the Jenkins API.

### How to Run

1.  **Navigate to the directory:**
    ```bash
    cd jenkinsmcp
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Configure Jenkins connection:**
    -   Create a `.env` file in the `jenkinsmcp/` directory.
    -   Add your Jenkins credentials:
        ```
        JENKINS_URL="http://your-jenkins-instance.com"
        JENKINS_USER="your-username"
        JENKINS_TOKEN="your-api-token"
        ```

4.  **Build and run the server:**
    ```bash
    npm run build
    npm start
    ```

---
