
## what it does
An advanced alert response automation solution that uses llms to analyze, classify, and respond to monitoring alerts intelligently and proactively. Working as an L1 operations agent, the system interprets problems, makes decisions, and triggers automation routines, significantly reducing incident response time and operational workload.

The most innovative aspect of the implementation is the use of function calling with Llama 3.2 model, executed through a local runtime. This technique allows the LLM to not only analyze text data, but also structure its responses as function calls with specific parameters.

The function calling implementation demonstrates a practical and efficient approach, defining tools the LLM can invoke with proper structure, parameters, and requirements.

The processing approach allows the LLM to not only analyze the problem but also recommend specific and parameterized actions to remedy it.

The system's effectiveness critically depends on prompt design, using a two-part approach with system prompt (defining context and expected behavior) and user prompt (structuring alert data and guiding decisions).


> [!TIP]
> All those are opensource tools, so if you wanna run it locally, just do it 🐳

## 📋 table of contents

- Architecture
- Components
- Operational Flow
- Requirements
- Setup and Installation
- Usage
- Customization
- Development
- Troubleshooting

## 🏗 architecture

This project implements a containerized microservices architecture:

```
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│             │        │             │        │             │
│  Monitoring │──────▶│     API     │───────▶│ Automation  │
│   System    │        │  Middleware │        │  Platform   │
│             │        │             │        │             │
└─────────────┘        └──────┬──────┘        └─────────────┘
                              │
                       ┌──────▼──────┐
                       │             │
                       │  Local LLM  │
                       │   Runtime   │
                       │             │
                       └─────────────┘
```

## 🧩 components

### API Middleware
Central core of the system that:
- Receives alerts from the monitoring system via webhook
- Sends prompts to the LLM model
- Processes LLM responses using function calling
- Triggers automation routines
- Provides debugging and monitoring endpoints

### monitoring system
Infrastructure monitoring that:
- Detects problems in the infrastructure
- Sends alerts to the API via webhook
- Stores history of problems and resolutions

### llm runtime
Language model execution service that:
- Runs the Llama 3.2 model locally
- Implements function calling for decision making
- Analyzes alert data and determines appropriate actions

### problem simulator
Container with monitoring agent configured to:
- Simulate different types of problems (CPU, disk, memory, services)
- Activate/deactivate problems via control scripts
- Test the complete alert and automation flow

## 🔄 operational flow

1. **Detection**: The monitoring system detects an infrastructure problem
2. **Alerting**: The monitoring system sends an alert via webhook to the API
3. **Processing**: The API formats the data and sends it to the LLM
4. **AI Analysis**: The LLM analyzes the data and determines which function to call
5. **Function Calling**: The model calls the appropriate function with specific parameters
6. **Automation**: The API translates the function call into an automation job
7. **Resolution**: The automation platform executes the job to resolve the problem
8. **Feedback**: Results are logged for future reference

## 📋 requirements

- Docker and Docker Compose
- Internet access (for initial image downloads)
- Minimum 8GB RAM (16GB recommended)
- At least 20GB of disk space

## 🛠 Customization

### configuring monitoring actions

The integration allows you to customize which alerts are sent to the API:

1. Access the monitoring system > Configuration > Actions
2. Edit the action "Send alerts to API"
3. Modify conditions and filters as needed

### adding new functions to the LLM

To add new functions that the AI can call:

1. Edit the LLM service file
2. Add your new function to the `_create_tools()` method
3. Update the mapping in the config file

```python
# Example of a new function
{
    "type": "function",
    "function": {
        "name": "check_database",
        "description": "Checks the health of a database",
        "parameters": {
            "type": "object",
            "properties": {
                "db_name": {
                    "type": "string",
                    "description": "Database name"
                },
                "check_type": {
                    "type": "string",
                    "description": "Type of check (connection, performance, etc)"
                }
            },
            "required": ["db_name"]
        }
    }
}
```

## 💻 development

### project structure

```
project/
├── app/                   # Main API code
│   ├── __init__.py
│   ├── api/               # Routers and endpoints
│   ├── core/              # Configurations and utilities
│   ├── models/            # Data models
│   └── services/          # External services
├── docker/                # Docker configurations
├── host/                  # Simulator scripts
├── scripts/               # Setup scripts
├── tests/                 # Tests
├── main.py                # API entry point
├── requirements.txt       # Dependencies
└── start_environment.sh   # Startup script
```

### code conventions

This project follows PEP-8 with the following conventions:
- Indentation: 4 spaces
- Maximum 79 characters per line
- Docstrings in all functions and classes
- snake_case for functions and variables
- CamelCase for classes
- UPPERCASE for constants

### development workflow

1. Set up a Python virtual environment
2. Install development dependencies
3. Implement your changes following conventions
4. Run tests
5. Build Docker image for testing
6. Submit a pull request

```bash
# Setting up development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r dev-requirements.txt

# Running tests
pytest

# Building image for testing
docker build -t api:dev -f docker/middleware/Dockerfile .
```

## 🔍 troubleshooting

### logs

To check service logs:

```bash
# API logs
docker logs api-middleware

# Monitoring server logs
docker logs monitoring-server

# Agent simulator logs
docker logs monitoring-agent-simulator

# LLM runtime logs
docker logs ollama
```