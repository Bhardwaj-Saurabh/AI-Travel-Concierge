# Travel Concierge Agent

> **📖 Purpose**: This is the main project README providing a high-level overview and quick start guide for the Travel Concierge Agent. Use this file to get started quickly and understand the project at a glance.

An intelligent travel planning agent built with Microsoft Semantic Kernel, Azure OpenAI, and Cosmos DB for vector RAG.

## 🚀 Quick Start

### Prerequisites
- Azure OpenAI service with GPT-4o-mini and text-embedding-3-small deployments
- Cosmos DB account with vector search enabled
- Bing Search API key

### Installation
```bash
cd project/starter
pip install -r requirements.txt
cp env.example .env
# Edit .env with your Azure credentials
```

### Usage

#### 💬 Chat Interface (Recommended)
```bash
python chat.py
```

#### Programmatic Usage
```python
from app.main import run_request
import json

result = run_request("I want to go to Paris from 2026-06-01 to 2026-06-08 with my BankGold card")
plan_data = json.loads(result)
print(plan_data["plan"]["destination"])
```

## 🏗️ Architecture

- **Semantic Kernel**: Tool orchestration and state management
- **Azure OpenAI**: GPT-4o-mini for chat and text-embedding-3-small for embeddings
- **Memory Systems**: Short-term and long-term memory for context management
- **Cosmos DB**: Vector RAG for long-term memory and knowledge retrieval
- **Class-Based Tools**: Modular tool architecture (WeatherTools, FxTools, SearchTools, CardTools)

## 🛠️ Development

### Testing & Progress Checking

#### **System Health Check**
```bash
# Comprehensive system health check
python app/scripts/system_check.py
```
This will verify:
- ✅ Azure OpenAI connectivity
- ✅ Cosmos DB connection
- ✅ All tool functionality
- ✅ Environment configuration
- ✅ Memory systems

#### **Unit Testing**
```bash
# Run all unit tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_models.py -v      # Data models
python -m pytest tests/test_tools.py -v       # Tool functionality
python -m pytest tests/test_state.py -v       # State management
python -m pytest tests/test_memory.py -v      # Memory systems
```

#### **Comprehensive Test Suite**
```bash
# Run all tests including health checks
python run_tests.py

# Run with different options
python run_tests.py --unit --verbose          # Unit tests only
python run_tests.py --quick                   # Quick tests only
```

#### **Progress Tracking**
- **Green checkmarks (✅)** in system_check.py output indicate working components
- **All tests passing** means your system is ready for development
- **Failed tests** will show specific issues to fix

### Project Structure
```
app/
├── main.py                 # Main entry point with SK integration
├── models.py              # Pydantic schemas
├── synthesis.py           # AI synthesis and JSON generation
├── state.py               # Enhanced agent state machine (8 phases)
├── memory.py              # Short-term memory system
├── long_term_memory.py    # Long-term memory with Cosmos DB
├── tools/                 # Class-based tool implementations
├── rag/                   # Vector RAG system
├── eval/                  # Evaluation harness
└── utils/                 # Utility modules
```

## 📚 Documentation

- **[app/README.md](app/README.md)** - Complete technical reference with API docs, data models, and tool functions
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - Step-by-step learning guide for students with development phases

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section in app/README.md
- Review the evaluation results
- Run health checks
- Check Azure service status