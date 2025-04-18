# VentureAI - VC Interview Simulation

A platform for conducting virtual venture capital interviews with AI-powered analysis and feedback.

## API Status

The API is available at:

```
https://ventureai-840537625469.us-central1.run.app
```

## Client Tools

### Fixed Client

A new fixed client is available that works with the latest API. It provides a simple command-line interface for conducting VC interviews:

```bash
python fixed_client.py --url https://ventureai-840537625469.us-central1.run.app
```

See `CLIENT_README.md` for detailed usage instructions.

### Original Clients

The original client tools are still available but may need fixes to work with the latest API:

- `simple_client.py` - Basic API status checker
- `interactive_interview.py` - Interactive VC interview simulator
- `interview_client.py` - Programmatic client with mock responses

## API Documentation

Full API documentation can be accessed at:

```
https://ventureai-840537625469.us-central1.run.app/docs
```

## Recent Fixes

Several issues were fixed to improve the API functionality:

- Fixed endpoint compatibility issues
- Improved error handling
- Enhanced request handling for both JSON and form data
- Added better data validation
- Created a fixed client that works with the latest API

For details on all fixes, see `FIXES.md`.
