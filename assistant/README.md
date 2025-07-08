# MB Personal Assistant

A Streamlit-based chat application that integrates with local LLMs through Ollama to provide conversational AI capabilities with support for multimodal inputs.

## Features

- **Multiple Model Support**: Choose between different Ollama models (gemma3:1b, gemma3:27b, llava)
- **Multimodal Capabilities**: Upload and analyze images with models like llava
- **Document Processing**: Upload and analyze PDF documents
- **Interactive Chat Interface**: User-friendly chat interface with streaming responses
- **Response Time Tracking**: Measures and displays the time taken to generate responses

## Requirements

- Python 3.8+
- Ollama running locally or on a remote server

## Installation

1. Clone this repository
2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Set up Ollama with the required models:

```bash
ollama pull gemma3:1b
ollama pull gemma3:27b
ollama pull llava
```

## Configuration

Create a `.env` file in the project root with the following variables:

```
OLLAMA_HOST=http://localhost:11434
```

You can customize the Ollama host if you're running it on a different machine or port.

## Usage

1. Start the Streamlit application:

```bash
streamlit run app.py
```

2. Access the application in your web browser (typically at http://localhost:8501)

3. Select a model from the sidebar

4. Start chatting with the AI assistant

5. Upload images or PDFs using the attachment button in the chat interface

## File Upload Support

- **Images**: JPG, JPEG, PNG
- **Documents**: PDF

## Advanced Usage

To run the application with custom environment variables without modifying the `.env` file:

```bash
OLLAMA_HOST=http://custom-host:11434 streamlit run app.py
```

## Troubleshooting

- If you encounter connection issues, verify that Ollama is running and accessible at the configured host
- For image processing issues, ensure that your Ollama installation includes models with multimodal support (like llava)
- Large PDF files may cause memory issues; consider splitting them into smaller files
