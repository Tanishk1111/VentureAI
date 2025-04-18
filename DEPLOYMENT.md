# VentureAI Deployment Guide

This document explains how to deploy the VentureAI application to Google Cloud Run.

## Prerequisites

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and configured
- [Git](https://git-scm.com/downloads) installed (for GitHub deployment)
- Google Cloud Project with billing enabled
- Required APIs enabled in your Google Cloud project:
  - Cloud Run API
  - Cloud Build API
  - Artifact Registry API
  - Vertex AI API
  - Speech-to-Text API
  - Text-to-Speech API

## Option 1: Deployment via GitHub Actions (Recommended)

1. **Push the code to GitHub**

   Run the existing script:

   ```
   deploy_to_github.bat
   ```

   This will:

   - Initialize a Git repository if not already done
   - Add and commit your files
   - Push them to your GitHub repository

2. **Set up GitHub Secrets**

   In your GitHub repository, go to Settings > Secrets and Variables > Actions and add:

   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GCP_SA_KEY`: The base64-encoded content of your Google Cloud service account key

3. **Verify Deployment**

   GitHub Actions will automatically:

   - Build the Docker container
   - Deploy it to Google Cloud Run
   - You can check the progress in the "Actions" tab of your repository

## Option 2: Direct Deployment to Google Cloud Run

1. **Build and deploy manually**

   ```bash
   # Set your project ID
   gcloud config set project YOUR_PROJECT_ID

   # Build the container
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ventureai

   # Deploy to Cloud Run
   gcloud run deploy ventureai \
     --image gcr.io/YOUR_PROJECT_ID/ventureai \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 1Gi \
     --cpu 1
   ```

## Important Files for Deployment

- `Dockerfile`: Defines the container configuration
- `.gcloudignore`: Specifies files that should not be uploaded to Google Cloud
- `app.yaml`: Configuration for Google App Engine (if using App Engine instead of Cloud Run)
- `.env`: Contains environment variables (make sure to set these in Cloud Run if not using GitHub Actions)

## Accessing the Deployed Application

After deployment, your application will be available at a URL like:

```
https://ventureai-HASH.a.run.app
```

## Environment Variables

Make sure the following environment variables are set in your deployment:

- `GOOGLE_API_KEY`: Your Google API key for Gemini and other services
- `PROJECT_ID`: Your Google Cloud project ID
- `ENVIRONMENT`: Set to "production" for deployed instances

## Troubleshooting

If you encounter issues:

1. Check Cloud Run logs
2. Verify that all required APIs are enabled
3. Ensure your service account has the necessary permissions
4. Make sure your environment variables are properly set

## Keeping Your API Key Secure

In production, avoid hardcoding your API key in files. Instead:

- For GitHub deployment: Use GitHub Secrets
- For direct deployment: Set environment variables in the Cloud Run service config
