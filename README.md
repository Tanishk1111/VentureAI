# VentureAI - VC Interview API

An API for conducting virtual VC interviews with AI-powered analysis and feedback using Gemini 1.5 Pro.

## Features

- Interview session management
- CV processing and question generation
- Sentiment analysis of responses
- Comprehensive interview feedback
- Text-to-speech and speech-to-text capabilities

## Deployment Options

### 1. Deploy via GitHub and Google Cloud Run (Recommended)

#### Prerequisites

- GitHub account
- Google Cloud Platform account
- Repository secrets configured (see below)

#### Setup GitHub Secrets

1. In your GitHub repository, go to Settings > Secrets and Variables > Actions
2. Add the following secrets:
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GCP_SA_KEY`: The entire content of your Google Cloud service account JSON key file (base64 encoded)

#### Deployment Process

1. Push your code to the `main` branch of your GitHub repository
2. GitHub Actions will automatically:

   - Build a Docker container
   - Push it to Google Container Registry
   - Deploy it to Google Cloud Run

3. Access your deployed application at the URL provided in the GitHub Actions logs

### 2. Manual Deployment to Google Cloud Run

#### Prerequisites

- Google Cloud Platform account
- Google Cloud SDK installed
- Docker installed

#### Setup

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/VentureAI.git
   cd VentureAI
   ```

2. Create a Service Account Key:

   - Go to GCP Console > IAM & Admin > Service Accounts
   - Create a service account with necessary permissions (Cloud Run Admin, Storage Admin)
   - Create a key in JSON format
   - Save the key to `keys/service-account.json`

3. Set up environment variables:
   - Copy `.env.sample` to `.env`
   - Update the values with your own settings

### Local Development

1. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   uvicorn main:app --reload
   ```

### Deploy to Google Cloud Run

1. Build and submit Docker image:

   ```
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ventureai
   ```

2. Deploy to Cloud Run:

   ```
   gcloud run deploy ventureai \
     --image gcr.io/YOUR_PROJECT_ID/ventureai \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="API_KEY=your_api_key,ENVIRONMENT=production"
   ```

3. Access the deployed API:
   ```
   https://ventureai-xxxxx-xx.a.run.app
   ```

## API Documentation

Once deployed, you can access the API documentation at:

```
https://ventureai-xxxxx-xx.a.run.app/docs
```
