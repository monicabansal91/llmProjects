import streamlit as st
from llama_index.core.llms import ChatMessage, TextBlock, ImageBlock
from llama_index.core.multi_modal_llms.generic_utils import load_image_urls
import logging
import time
import os
import tempfile
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from llama_index.llms.ollama import Ollama

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)

# Initialize chat history in session state if not already present
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Function to stream chat response based on selected model
def stream_chat(model, messages):
    try:
        ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        print(f"Using Ollama host: {ollama_host}")  # Debugging line to check Ollama host
        llm = Ollama(
            model=model, 
            request_timeout=120.0, 
            base_url=ollama_host
        ) 
        # Stream chat responses from the model
        resp = llm.stream_chat(messages)
        response = ""
        response_placeholder = st.empty()
        # Append each piece of the response to the output
        for r in resp:
            response += r.delta
            response_placeholder.write(response)
        # Log the interaction details
        logging.info(f"Model: {model}, Messages: {messages}, Response: {response}")
        return response
    except Exception as e:
        # Log and re-raise any errors that occur
        logging.error(f"Error during streaming: {str(e)}")
        raise e
    
def main():
    print(os.getenv('OLLAMA_HOST', 'http://localhost:11434'))
    st.title("Chat with LLMs Models")  # Set the title of the Streamlit app
    logging.info("App started")  # Log that the app has started
    
    # Apply custom CSS for better UI
    st.markdown("""
    <style>
    .stChatFloatingInputContainer {
        padding-right: 40px !important;
    }
    .upload-btn-container {
        position: absolute;
        bottom: 0.5rem;
        right: 0.5rem;
        z-index: 100;
    }
    .upload-btn-container .stFileUploader {
        width: 3rem;
    }
    .upload-btn-container [data-testid="stFileUploader"] {
        width: 38px !important;
    }
    .upload-btn-container [data-testid="stFileUploader"] button {
        padding: 0.25rem;
        background-color: transparent;
        border: none;
    }
    .upload-btn-container [data-testid="stFileUploader"] button:hover {
        background-color: rgba(128, 128, 128, 0.2);
        border-radius: 4px;
    }
    .upload-btn-container [data-testid="stFileUploader"] [data-testid="stFileUploadDropzone"] {
        min-height: 0;
        padding: 0;
        margin: 0;
    }
    .upload-btn-container [data-testid="stFileUploader"] small {
        display: none;
    }
    div[data-testid="stImage"] {
        text-align: center;
        max-width: 100%;
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar for model selection
    model = st.sidebar.selectbox("Choose a model", ["gemma3:1b", "gemma3:27b", "llava"])
    logging.info(f"Model selected: {model}")
    
    # Initialize file content variable
    file_content = None
    
    # Initialize session state for uploaded files if it doesn't exist
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'file_content' not in st.session_state:
        st.session_state.file_content = None
    if 'file_type' not in st.session_state:
        st.session_state.file_type = None

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input for user prompt
    prompt = st.chat_input("Your question")
    
    # Add file uploader as a floating button
    with st.container():
        st.markdown('<div class="upload-btn-container">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Attach file", type=["jpg", "jpeg", "png", "pdf"], key="chat_file_uploader", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Process uploaded file if any
    if uploaded_file is not None:
        file_type = uploaded_file.type
        
        # Only process if this is a new file or different from the previous one
        if st.session_state.uploaded_file is None or uploaded_file.name != st.session_state.uploaded_file.name:
            st.session_state.uploaded_file = uploaded_file
            st.session_state.file_type = file_type
            
            if file_type.startswith('image/'):
                # Save the uploaded file to a temporary location
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type.split('/')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                st.session_state.file_content = tmp_path
                
                # Show preview in sidebar
                st.sidebar.header("Uploaded Image")
                st.sidebar.image(uploaded_file, caption=uploaded_file.name, use_column_width=True)
                st.sidebar.success(f"Image uploaded successfully")
                
            elif file_type == 'application/pdf':
                try:
                    # Read the PDF file
                    pdf_reader = PdfReader(uploaded_file)
                    text = ""
                    
                    # Extract text from all pages
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    
                    st.session_state.file_content = text
                    
                    # Show preview in sidebar
                    st.sidebar.header("Uploaded PDF")
                    st.sidebar.success(f"PDF processed successfully: {uploaded_file.name}")
                    st.sidebar.text_area("PDF Content Preview", text[:500] + "..." if len(text) > 500 else text, height=200)
                except Exception as e:
                    logging.error(f"Error processing PDF: {str(e)}")
                    st.error(f"Error processing PDF: {str(e)}")
        
        # Use the stored file content
        file_content = st.session_state.file_content
    
    # Process user input when submitted
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        logging.info(f"User input: {prompt}")

        # Display the new user message
        with st.chat_message("user"):
            st.write(prompt)

        # Generate a new response if the last message is not from the assistant
        if st.session_state.messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):
                start_time = time.time()  # Start timing the response generation
                logging.info("Generating response")

                with st.spinner("Writing..."):
                    try:
                        # Prepare messages for the LLM and stream the response
                        messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in st.session_state.messages]
                        
                        # Add file content to the message if available
                        if file_content:
                            # Check if it's an image file path
                            if isinstance(file_content, str) and os.path.isfile(file_content) and any(file_content.endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
                                # Add the image content to the last user message
                                last_message = messages[-1]
                                
                                try:
                                    # Debug output to verify the image path
                                    print(f"Using image path: {file_content}")                                    
                                    # Create the chat message with the proper format for Ollama
                                    messages[-1] = ChatMessage(
                                        role=last_message.role,
                                        blocks=[
                                            TextBlock(text=last_message.content),
                                            ImageBlock(path=file_content),
                                        ],
                                    )
                                except Exception as img_e:
                                    print(f"Error processing image: {str(img_e)}")
                                    st.warning(f"Could not process image: {str(img_e)}")
                            
                            elif isinstance(file_content, str):  # It's text content from a PDF
                                # Add the PDF content to the last user message
                                last_message = messages[-1]
                                messages[-1] = ChatMessage(
                                    role=last_message.role,
                                    content=f"{last_message.content}\n\nDocument content:\n{file_content[:2000]}..."
                                )
                        
                        response_message = stream_chat(model, messages)
                        duration = time.time() - start_time  # Calculate the duration
                        response_message_with_duration = f"{response_message}\n\nDuration: {duration:.2f} seconds"
                        st.session_state.messages.append({"role": "assistant", "content": response_message_with_duration})
                        st.write(f"Duration: {duration:.2f} seconds")
                        logging.info(f"Response: {response_message}, Duration: {duration:.2f} s")

                    except Exception as e:
                        # Handle errors and display an error message
                        st.session_state.messages.append({"role": "assistant", "content": str(e)})
                        st.error("An error occurred while generating the response.")
                        logging.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()