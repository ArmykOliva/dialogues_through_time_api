# Dialogues Through Time - FastAPI Backend

## Overview
This repository contains the FastAPI backend module for "Dialogues Through Time," an immersive educational game that combines historical education with interactive AI dialogues. Our backend manages game states, processes AI dialogues, and integrates with Azure services.

![Dialogues Through Time Game Image](https://github.com/ArmykOliva/dialogues_through_time_api/blob/main/pictures/Screenshot_1.png?raw=true)

[Link to Unity frontend](https://github.com/bentoBAUX/Dialogues-Through-Time)

[YouTube video overview](https://youtu.be/FxS6ehhNVrc)

## Features
- **AI Dialogue Management**
- **LLM Constraining System**
- **Game State Management**
- **Azure OpenAI Integration**

## Getting Started

### Prerequisites
- Python 3.8+
- FastAPI
- Uvicorn
- Azure account and Redis service

### Installation
1. Clone the repository
2. Navigate to the project directory
3. Install the required packages

### Environment Setup
Create a `.env` file in the root directory with the following structure:
```env
AZURE_API_KEY=YourAzureApiKeyHere
API_KEY=YourApiKeyHere
REDIS_PASSWORD=YourRedisPasswordHere
```
*Note: The above keys are placeholders. Replace them with your actual keys.*

### Running the Server
Run the server using Uvicorn:
```bash
uvicorn main:app --reload
```

## Usage
Access the backend API at `http://localhost:8000`.

## Documentation
For a detailed explanation of the backend setup and functionalities, refer to our [YouTube video overview](https://youtu.be/FxS6ehhNVrc).

## Architecture
- **Unity Frontend Integration**
- **Azure Redis Cache**
- **LLM Constraining Module**
- **Azure OpenAI Service**

## License
This project is licensed under the [MIT License](LICENSE).
