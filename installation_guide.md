# Installation Guide

This guide explains how to install, configure, and run the RAG Application on your local machine.

---

# System Requirements

Before installing the application, ensure your system meets the following requirements:

* Python 3.10 or later
* Git
* Internet connection for Google Gemini API and the embedding model

---

# Step 1: Clone the Repository

Clone the project from GitHub.

```bash
git clone <repository-url>
cd <project-folder>
```

Or download the project as a ZIP file and extract it.

---

# Step 2: Create a Virtual Environment

Creating a virtual environment is recommended to isolate project dependencies.

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

After activation, your terminal should display the virtual environment name.

---

# Step 3: Install Required Packages

Install all project dependencies using pip.

```bash
pip install -r requirements.txt
```

This installs Flask, LangChain, ChromaDB, Sentence Transformers, Gemini integration, and all other required libraries.

---

# Step 4: Get a Gemini API Key

Create a key in [Google AI Studio](https://aistudio.google.com/apikey). Use the free tier and do not enable paid billing if you want to avoid charges. Free-tier eligibility and quotas depend on your account and region.

# Step 5: Configure Environment Variables

Create a file named `.env` in the project's root directory.

Add your AI Studio API key and a Flask secret key:

```env
GOOGLE_API_KEY=your_google_ai_studio_api_key
SECRET_KEY=your_random_secret
GEMINI_MODEL=gemini-3.5-flash-lite
```

The app does not switch to a paid model automatically. If you reach the free-tier quota, requests may be rate-limited until the quota resets.

---

# Step 6: Run the Application

Start the Flask application by running:

```bash
python app.py
```

If the installation is successful, the application will start without errors.

Open your browser and navigate to:

```
http://localhost:5000
```

---

# Step 7: Login

The application includes demo accounts for testing.

| Username | Password | Role  |
| -------- | -------- | ----- |
| admin    | admin123 | Admin |
| demo     | demo123  | User  |

You may also create a new account using the registration page.

---

# Step 8: Upload Documents

After logging in:

1. Open the **Upload Documents** page.
2. Select one or more supported files.
3. Upload the documents.
4. Wait for processing to complete.

During processing, the application:

* Extracts document text
* Splits text into chunks
* Generates embeddings
* Stores embeddings in ChromaDB

---

# Step 9: Chat with Your Documents

Once processing is complete:

1. Open the **Chat** page.
2. Ask questions about the uploaded documents.
3. The application retrieves the most relevant document chunks.
4. Gemini generates a grounded response with citations.

---

# Running Tests

Run the project's test suite using:

```bash
pytest tests/ -v
```

---

# Supported File Formats

The application supports the following document types:

* PDF (.pdf)
* Microsoft Word (.docx)
* Text (.txt)
* Markdown (.md)

---

# Troubleshooting

### Missing Dependencies

If a package is missing, reinstall the dependencies:

```bash
pip install -r requirements.txt
```

### Gemini API Key or Free-Tier Quota

Verify that `GOOGLE_API_KEY` is a valid Google AI Studio key and that Gemini API access is available for your account and region. If you reach the free-tier quota, wait for it to reset; the application does not fall back to a paid model.

### Model Download

The Sentence Transformer model is downloaded automatically during the first execution. Depending on your internet connection, this may take a few minutes.

### Port Already in Use

If port **5000** is occupied, stop the conflicting application or configure Flask to use a different port.

---

# Uninstall

To remove the application:

1. Delete the project folder.
2. Remove the virtual environment (`venv`).
3. Delete the local ChromaDB database if it is no longer needed.

No additional system configuration is required.
