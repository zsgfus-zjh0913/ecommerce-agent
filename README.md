# Ecommerce AI Agent

An AI-powered customer service agent built with FastAPI and DeepSeek API, designed for fashion e-commerce stores.

## Core Features

- **FAQ Knowledge Base Search** — Answers common questions about return policies, shipping times, freight costs, and payment methods
- **Order Inquiry** — Query order status and logistics information by order ID or phone number
- **Return Processing** — Create return/refund or exchange requests with automated return slips and shipping instructions
- **Product Recommendation** — Search and recommend clothing, footwear, and accessories based on user needs

## Technical Architecture

- Built with **FastAPI** for RESTful API and web interface
- Integrates **DeepSeek Chat** model via OpenAI-compatible protocol
- Supports **Tool Use** loop (up to 5 rounds) for intelligent tool selection
- **SSE (Server-Sent Events)** for real-time streaming chat responses
- Built-in conversation memory with 20-turn context window

## Quick Start

1. Set your DeepSeek API key:
   ```bash
   export DEEPSEEK_API_KEY="your-api-key"
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Access the web interface at: `http://localhost:8002`

## API Endpoints

- `GET /` — Web chat interface
- `POST /api/chat` — SSE streaming chat API
- `POST /api/reset` — Reset conversation context
- `GET /api/health` — Health check