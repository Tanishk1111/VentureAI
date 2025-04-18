# VentureAI Fixed Client

A simple, fixed client for interacting with the VentureAI Interview API.

## Getting Started

### Prerequisites

- Python 3.7+
- Requests library (`pip install requests`)

### Usage

The client can be run directly from the command line:

```bash
python fixed_client.py
```

By default, it will connect to a local server running at http://localhost:8080.

### Command Line Options

- `--url`: API base URL (default: http://localhost:8080)
- `--questions`: Number of questions in the interview (default: 3)
- `--cv`: Path to a CV file to upload (optional)

Example:

```bash
python fixed_client.py --url https://ventureai-840537625469.us-central1.run.app --questions 5
```

## Features

The client supports the following features:

1. Creating interview sessions
2. Getting interview questions
3. Submitting responses to questions
4. Getting feedback on the interview

## Troubleshooting

If you're experiencing issues:

1. Ensure the API server is running
2. Check if you can access the API directly in a browser
3. Try running with the `--url` parameter to specify the correct API endpoint

## Example Workflow

1. Run the client: `python fixed_client.py`
2. The client will create a new interview session
3. You'll be presented with interview questions one by one
4. Type your responses to each question
5. After all questions are answered, you'll receive feedback on your interview

## Extending the Client

You can import the `FixedVentureAIClient` class into your own Python scripts:

```python
from fixed_client import FixedVentureAIClient

client = FixedVentureAIClient(base_url="https://your-api-url.com")
client.create_session()
question = client.get_next_question()
client.submit_response("Your response goes here")
feedback = client.get_feedback()
```
