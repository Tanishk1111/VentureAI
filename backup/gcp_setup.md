# Google Cloud Platform Setup for VentureAI

This guide will help you set up your Google Cloud Platform (GCP) project and create a service account for GitHub Actions deployment.

## 1. Set Up GCP Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing project.
3. Make note of your Project ID - you'll need it for GitHub Secrets.

## 2. Enable Required APIs

1. Navigate to "APIs & Services" > "Library"
2. Search for and enable the following APIs:
   - Cloud Run API
   - Cloud Build API
   - Container Registry API
   - Artifact Registry API
   - Cloud Storage API

## 3. Create a Service Account

1. Go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Enter a name and description for your service account
4. Click "Create and Continue"
5. Add the following roles:
   - Cloud Run Admin
   - Storage Admin
   - Cloud Build Editor
   - Service Account User
   - Artifact Registry Writer
6. Click "Continue" and then "Done"

## 4. Create and Download a Service Account Key

1. Find your newly created service account in the list
2. Click on the account email to view details
3. Go to the "Keys" tab
4. Click "Add Key" > "Create new key"
5. Choose JSON format
6. Click "Create" to download the key file

## 5. Set Up GitHub Secrets

1. Base64 encode the service account key file:

   - Windows PowerShell: `[Convert]::ToBase64String([IO.File]::ReadAllBytes("path\to\your-key.json"))`
   - Linux/macOS: `cat path/to/your-key.json | base64`

2. In your GitHub repository:
   - Go to "Settings" > "Secrets and variables" > "Actions"
   - Add a new secret `GCP_PROJECT_ID` with your project ID
   - Add a new secret `GCP_SA_KEY` with the base64-encoded key content

## 6. Push to GitHub

After setting up these secrets, push your code to GitHub to trigger the deployment pipeline. The GitHub Actions workflow will automatically deploy your application to Google Cloud Run.
