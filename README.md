

## what it does
An advanced alert response automation solution that uses Large Language Models (LLMs) to analyze, classify, and respond to monitoring alerts intelligently and proactively. Working as an L1 operations agent, the system interprets problems, makes decisions, and triggers automation routines, significantly reducing incident response time and operational workload.

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

### LLM Runtime
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

## ⚙️ setup and installation

### quick installation

```bash
# Clone the repository
git clone https://github.com/username/repo-name.git
cd repo-name

# Start the environment
chmod +x start_environment.sh
./start_environment.sh
```

The start_environment.sh script will:
1. Check prerequisites
2. Build the API image
3. Start all containers via Docker Compose
4. Download the Llama 3.2 model
5. Configure the integration between the monitoring system and API
6. Add simulator host to the monitoring system

### manual configuration

If you prefer to configure manually:

```bash
# Build the API image
docker build -t api-middleware -f docker/middleware/Dockerfile .

# Start containers
docker compose -f docker/docker-compose.yaml up -d

# Verify everything is working
docker compose -f docker/docker-compose.yaml ps

# Download the Llama 3.2 model
docker exec -i ollama ollama pull llama3.2

# Configure monitoring integration
python3 scripts/setup_media_type.py
python3 scripts/add_simulator_host.py
```

## 🖥️ usage

### accessing services

- **API Middleware**: http://localhost:8000
  - API Documentation: http://localhost:8000/docs
  - Health Check: http://localhost:8000/api/v1/health

- **Monitoring System**: http://localhost:8080
  - User: `Admin`
  - Password: `zabbix`

- **LLM Runtime**: http://localhost:11434

### simulating problems

```bash
# Access the simulator container
docker exec -it monitoring-agent-simulator bash

# Activate disk full problem
/etc/scripts/control.sh disk on

# Activate high CPU problem
/etc/scripts/control.sh cpu on

# Activate high memory problem
/etc/scripts/control.sh memory on

# Activate service down problem
/etc/scripts/control.sh service on

# To deactivate any problem
/etc/scripts/control.sh [problem] off
```

### testing alert processing

```bash
# Test with disk full alert
python3 tests/simulate_payload.py disk_full

# Test with service down alert
python3 tests/simulate_payload.py service_down

# Test with high CPU alert
python3 tests/simulate_payload.py high_cpu
```

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

The most innovative aspect of the implementation is the use of function calling with Llama 3.2 model, executed through a local runtime. This technique allows the LLM to not only analyze text data, but also structure its responses as function calls with specific parameters.

The function calling implementation demonstrates a practical and efficient approach, defining tools the LLM can invoke with proper structure, parameters, and requirements.

The processing approach allows the LLM to not only analyze the problem but also recommend specific and parameterized actions to remedy it.

The system's effectiveness critically depends on prompt design, using a two-part approach with system prompt (defining context and expected behavior) and user prompt (structuring alert data and guiding decisions).

Using local LLM runtime provides important advantages:
- **Data privacy**: Sensitive monitoring data never leaves the controlled environment
- **Reduced latency**: Local execution eliminates network delays
- **Offline operation**: The system can function in air-gapped environments
- **Customization**: Possibility of fine-tuning with proprietary operations data

The modular REST API-based architecture facilitates:
- Component substitution
- Model updates
- Addition of new capabilities without rewriting the system

The system demonstrates applicability in various common operations scenarios:
1. Infrastructure resource management
2. Service stability
3. Advanced triage

The implementation presents important challenges:
1. Hardware requirements for local LLM execution
2. Model accuracy for correct problem identification
3. Continuous adaptation to changing infrastructure environments

This project represents a practical implementation of AIOps based on open source components, demonstrating how LLMs can be applied to real IT operations problems. As language models continue to evolve, we can anticipate deeper integration with observability systems, enhanced diagnostic capabilities, greater autonomy in remediation, and continuous learning from human interventions.