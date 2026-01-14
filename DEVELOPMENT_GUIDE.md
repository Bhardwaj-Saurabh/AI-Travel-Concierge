# 🚀 Development Guide for Students

> **📖 Purpose**: This is a step-by-step learning guide designed for students working on the Travel Concierge Agent project. Use this file to follow a structured development process, learn the system components, and understand when to use different tools and interfaces.

This guide walks you through the development process step-by-step, showing you exactly when and how to use the chat interface.

## 📋 Development Phases

### Phase 1: Setup & Environment (Day 1)
**Goal**: Get your development environment ready

1. **Clone and Install**
   ```bash
   git clone <repository-url>
   cd project/starter
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Azure credentials
   ```

3. **Test Basic Setup**
   ```bash
   # Check if everything is configured
   python app/scripts/system_check.py
   
   # Run unit tests to verify everything works
   python -m pytest tests/ -v
   ```

**✅ You're ready when**: 
- All health checks show green checkmarks (✅)
- All unit tests pass
- No error messages in the output

---

### Phase 2: Understanding the Codebase (Day 2-3)
**Goal**: Learn how the agent works

1. **Explore the Structure**
   ```bash
   # Look at the main entry point
   cat app/main.py

   # Check the state management
   cat app/state.py

   # See the tools
   ls app/tools/
   ```

2. **Run Unit Tests**
   ```bash
   # Test individual components
   python -m pytest tests/test_models.py -v
   python -m pytest tests/test_state.py -v
   python -m pytest tests/test_tools.py -v
   python -m pytest tests/test_memory.py -v
   ```

3. **Try the Chat Interface** 🎯
   ```bash
   # Start chatting with the agent
   python chat.py
   ```

**✅ You're ready when**: 
- All unit tests pass
- You can successfully chat with the agent
- The agent responds with formatted travel plans

---

### Phase 3: Building Your Own Agent (Day 4-7)
**Goal**: Create your own agent features

1. **Add New Tools**
   ```bash
   # Create a new tool following the class-based pattern
   touch app/tools/my_tool.py
   # Follow the pattern in existing tools (WeatherTools, FxTools, etc.)
   ```

2. **Test Your Tools**
   ```bash
   # Test individual tools
   python -c "from app.tools.my_tool import MyTool; print(MyTool().my_function())"
   
   # Add tests for your tool
   python -m pytest tests/test_tools.py::TestMyTool -v
   ```

3. **Integrate with Chat**
   ```bash
   # Update main.py to include your tool in the kernel
   # Test through chat interface
   python chat.py
   ```

**✅ You're ready when**: Your new tools work in the chat interface

---

### Phase 4: Advanced Features (Day 8-10)
**Goal**: Implement advanced agent capabilities

1. **Memory Systems**
   ```bash
   # Test short-term memory
   python -c "from app.memory import ShortTermMemory; m = ShortTermMemory(); print(m)"

   # Test long-term memory
   python -c "from app.long_term_memory import LongTermMemory; m = LongTermMemory(); print(m)"
   ```

2. **RAG System**
   ```bash
   # Test knowledge retrieval
   python -c "from app.rag.retriever import retrieve; print('RAG system ready')"
   
   # Test knowledge base
   python -c "from app.knowledge_base import get_card_recommendation; print('Knowledge base ready')"
   ```

3. **Full Integration Testing**
   ```bash
   # Run comprehensive tests
   python run_tests.py
   
   # Run all unit tests
   python -m pytest tests/ -v
   
   # Check system health
   python app/scripts/system_check.py
   ```

**✅ You're ready when**: 
- All tests pass (unit tests + health checks)
- Advanced features work correctly
- System health check shows all green checkmarks (✅)

---

## 🎯 When to Use the Chat Interface

### ✅ **Use Chat Interface When:**
- **Testing your agent** - See how it responds to real user input
- **Debugging issues** - Interactive testing helps identify problems
- **Demonstrating capabilities** - Show off your agent's features
- **Learning the system** - Understand how components work together
- **Validating changes** - Make sure your modifications work correctly

### ❌ **Don't Use Chat Interface When:**
- **Running automated tests** - Use `pytest` instead
- **Checking system health** - Use `system_check.py` instead
- **Batch processing** - Use programmatic API instead
- **CI/CD pipelines** - Use test scripts instead

## 🛠️ Development Workflow

### Daily Development Cycle
```bash
# 1. Start your day - check system health
python app/scripts/system_check.py
# Look for: All green checkmarks (✅)

# 2. Make changes to your code
# ... edit files ...

# 3. Test your changes
python -m pytest tests/ -v
# Look for: All tests passing

# 4. Test with chat interface
python chat.py
# Look for: Agent responds with formatted plans

# 5. Run full test suite
python run_tests.py
# Look for: All tests + health checks passing
```

### Debugging Workflow
```bash
# 1. Identify the problem
python chat.py
# ... reproduce the issue ...

# 2. Check system health
python app/scripts/system_check.py
# Look for: Red X marks (❌) indicating failed components

# 3. Run specific tests
python -m pytest tests/test_tools.py -v
# Look for: Specific test failures and error messages

# 4. Test individual components
python -c "from app.tools.weather import WeatherTools; print(WeatherTools().get_weather(48.8566, 2.3522))"
python -c "from app.tools.fx import FxTools; print(FxTools().convert_fx(100, 'USD', 'EUR'))"

# 5. Fix and test again
python -m pytest tests/ -v
python app/scripts/system_check.py
python chat.py
```

## 📚 Learning Resources

### Understanding the Code
- **`app/main.py`** - Main agent orchestration with Semantic Kernel
- **`app/state.py`** - Enhanced state management system with 8 phases
- **`app/tools/`** - Class-based tool implementations (WeatherTools, FxTools, etc.)
- **`app/memory.py`** - Short-term memory system
- **`app/long_term_memory.py`** - Long-term memory system with Cosmos DB
- **`app/models.py`** - Pydantic data models (TripPlan, Weather, etc.)
- **`app/synthesis.py`** - AI synthesis and JSON generation
- **`app/rag/`** - Vector RAG system for knowledge retrieval

### Testing Your Code
- **`tests/`** - Unit and integration tests
- **`run_tests.py`** - Comprehensive test runner
- **`app/scripts/system_check.py`** - System health checks

### Interacting with Your Agent
- **`chat.py`** - CLI chat interface (recommended)
- **`app/main.py`** - Programmatic API with `run_request()` function

## 🚨 Common Issues & Solutions

### "Module not found" errors
```bash
# Make sure you're in the right directory
pwd
# Should be: .../project/starter

# Check Python path
python -c "import sys; print(sys.path)"
```

### "Environment variables not found"
```bash
# Check your .env file
cat .env

# Test environment loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.environ.get('AZURE_OPENAI_ENDPOINT'))"
```

### "Chat interface not working"
```bash
# Check if all dependencies are installed
pip list | grep semantic-kernel

# Test basic functionality
python -c "from app.main import run_request; print('Main module loaded')"
```

## 🎉 Success Criteria

You've successfully completed the development when:

1. ✅ **Environment Setup**: 
   - `python app/scripts/system_check.py` shows all green checkmarks (✅)
   - No error messages in system health check

2. ✅ **Basic Functionality**: 
   - `python chat.py` works and responds with formatted travel plans
   - Agent can handle different travel requests

3. ✅ **Unit Tests**: 
   - `python -m pytest tests/ -v` shows all tests passing
   - No test failures or errors

4. ✅ **Integration**: 
   - `python run_tests.py` passes all tests and health checks
   - Your custom features work in the chat interface

5. ✅ **Documentation**: 
   - You understand how all components work together
   - You can debug issues using the provided tools

**Progress Tracking Tips:**
- Use `python app/scripts/system_check.py` to verify system health
- Use `python -m pytest tests/ -v` to verify code functionality
- Use `python chat.py` to test end-to-end functionality
- Look for green checkmarks (✅) and "PASSED" messages as success indicators

**Happy coding! 🚀**