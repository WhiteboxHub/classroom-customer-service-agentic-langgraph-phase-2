# XYZ Corp Customer Call Center Solution - Agentic AI

## Overview
This repository contains the implementation of an Agentic AI solution for XYZ Corp's Customer Call Center. The system uses a graph-based architecture with specialized agents for Claims, Billing, and Scheduling.

## Architecture
The system is built on the following core components:
- **Core Engine**: Cyclic State Graph execution engine.
- **Memory**: Short-term (Postgres) and Long-term (Vector DB) memory.
- **Security**: PII scrubbing, Auth context, and Audit logging.
- **Agents**: Specialized domain agents (Claims, Billing, Scheduling).

## Getting Started

### Prerequisites
- Python 3.10+
- Docker & Docker Compose

### Installation
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
4. Start infrastructure:
   ```bash
   docker-compose up -d
   ```
