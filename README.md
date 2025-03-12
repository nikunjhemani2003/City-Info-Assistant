# City Information Assistant

## Overview

The **City Information Assistant** is an AI-powered chatbot built using **Streamlit**, **LlamaIndex**, and **OpenAI's GPT-3.5-Turbo**. It allows users to query city statistics using SQL and get semantic answers about US cities through an LLM-based tool.

## Features

- **Query City Statistics** using SQL database (SQLite)
- **Semantic Search on Cities** using Llama Cloud Tool
- **Natural Language Understanding** powered by OpenAI
- **Streamlit-based Web Interface**
- **Logging & Observability** using Arize Phoenix

---

## Installation

### Prerequisites

Ensure you have the following installed:

- **Python 3.8+**
- **pipenv (recommended) or virtualenv**
- **Streamlit**
- **SQLAlchemy**
- **LlamaIndex**
- **OpenAI API Key**

### Step 1: Clone the Repository

```bash
git clone https://github.com/nikunjhemani2003/City-Info-Assistant.git
cd City-Info-Assistant
```

### Step 2: Set up Virtual Environment

Using **pipenv** (recommended):

```bash
pipenv install --python 3.8
pipenv shell
```

Using **venv**:

```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate  # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

#### **Example `requirements.txt`**

```
streamlit>=1.32.0
llama-index-core>=0.10.25.post2
llama-index>=0.10.0
llama-index-embeddings-openai>=0.1.3
llama-index-indices-managed-llama-cloud>=0.1.3
llama-index-readers-file
llama-index-callbacks-arize-phoenix>=0.1.3
jupyter
nest-asyncio>=1.5.8
sqlalchemy>=2.0.0
openai>=1.12.0
python-dotenv>=1.0.0
termcolor>=2.3.0
```

---

## Environment Variables

Create a `.env` file in the root directory and add the following keys:

```ini
OPENAI_API_KEY=your_openai_api_key
PHOENIX_API_KEY=your_phoenix_api_key
LLAMA_CLOUD_API_KEY=your_llama_cloud_api_key
```

You can obtain your OpenAI API Key from [OpenAI API](https://platform.openai.com/api-keys).

---

## Running the Application

To start the **City Information Assistant**, run:

```bash
streamlit run streamlit_app.py
```

This will launch the chatbot in your default web browser.

---

## Project Workflow

1. **User Input:** The user asks a question about a US city.
2. **Router Workflow:** The AI determines whether to use SQL queries or LLM-based retrieval.
3. **Query Execution:**
   - If the question requires structured data, the SQL tool queries the city database.
   - Otherwise, the Llama Cloud tool retrieves semantic information.
4. **Response Generation:** The AI formats and returns an answer.
5. **Chat History:** All interactions are stored in session state.

---

## Contributing

1. **Fork the Repository**
2. **Clone Your Fork**
   ```bash
   git clone https://github.com/your-username/City-Info-Assistant.git
   cd City-Info-Assistant
   ```
3. **Create a New Branch**
   ```bash
   git checkout -b feature-branch
   ```
4. **Make Changes & Commit**
   ```bash
   git add .
   git commit -m "Add new feature"
   ```
5. **Push to GitHub & Create a Pull Request**
   ```bash
   git push origin feature-branch
   ```

Check existing examples and ensure your changes include a proper README if applicable.

---

## License

This project is licensed under the **MIT License**. Feel free to use and modify it.

For any queries, feel free to **open an issue** or **create a pull request**!
