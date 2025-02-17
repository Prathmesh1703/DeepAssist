import streamlit as st
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,
    ChatPromptTemplate
)
import threading

# Initialize Flask app for React frontend
app = Flask(__name__)
CORS(app)

# Initialize the chat engine
llm_engine = ChatOllama(
    model="deepseek-r1:1.5b",
    base_url="https://random-url.ngrok.io",
    temperature=0.3
)

# System prompt configuration
system_prompt = SystemMessagePromptTemplate.from_template(
    "You are an expert AI coding assistant. Format your responses as follows:\n\n"
    "### Solution\n"
    "Brief explanation of the approach\n\n"
    "### Code\n"
    "```[language]\n"
    "Your code here\n"
    "```\n\n"
    "### Explanation\n"
    "Concise explanation of the code\n\n"
    "IMPORTANT RULES:\n"
    "- Always use proper markdown formatting\n"
    "- Always specify the language in code blocks\n"
    "- Keep explanations clear and concise\n"
    "- Never show thinking process\n"
    "- Focus on practical implementation\n"
    "- Provide complete, working solutions"
)

# Message history for API
api_message_history = []

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message')
        
        # Add user message to history
        api_message_history.append({"role": "user", "content": user_message})
        
        # Build prompt chain
        prompt_sequence = [system_prompt]
        for msg in api_message_history:
            if msg["role"] == "user":
                prompt_sequence.append(HumanMessagePromptTemplate.from_template(msg["content"]))
            elif msg["role"] == "ai":
                prompt_sequence.append(AIMessagePromptTemplate.from_template(msg["content"]))
        
        prompt_chain = ChatPromptTemplate.from_messages(prompt_sequence)
        
        # Generate response
        processing_pipeline = prompt_chain | llm_engine | StrOutputParser()
        response = processing_pipeline.invoke({})
        
        # Add AI response to history
        api_message_history.append({"role": "ai", "content": response})
        
        return jsonify({
            'response': response
        })

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

def run_flask():
    app.run(port=5000)

def run_streamlit():
    # Streamlit title and caption
    st.title("DeepAssist Code Companion")
    st.caption("Generative AI application using deepseek 1.5b")

    # Sidebar: Model configuration
    selected_model = st.sidebar.selectbox(
        "Choose Model",
        ["deepseek-r1:1.5b"],
        index=0
    )

    st.sidebar.divider()

    # Initialize session state for message log
    if "message_log" not in st.session_state:
        st.session_state.message_log = [
            {"role": "ai", "content": "Hi! I'm DeepSeek. How can I help you code today? 💻"}
        ]

    # Initialize popup state
    if "popup" not in st.session_state:
        st.session_state.popup = {
            "show": False,
            "content": "",
            "type": "info"
        }

    # Display chat messages
    chat_container = st.container()
    with chat_container:
        # Show popup if active
        if st.session_state.popup["show"]:
            with st.expander("Latest Solution", expanded=True):
                st.markdown(st.session_state.popup["content"])
                if st.button("Close Solution"):
                    st.session_state.popup["show"] = False
                    st.session_state.popup["content"] = ""
                    st.rerun()
        
        # Display message history
        for message in st.session_state.message_log:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input for user queries
    user_query = st.chat_input("Type your coding question here...")

    # Handle user input
    if user_query:
        # Add user message to log
        st.session_state.message_log.append({"role": "user", "content": user_query})
        
        # Generate AI response
        with st.spinner("Generating solution..."):
            prompt_sequence = [system_prompt]
            for msg in st.session_state.message_log:
                if msg["role"] == "user":
                    prompt_sequence.append(HumanMessagePromptTemplate.from_template(msg["content"]))
                elif msg["role"] == "ai":
                    prompt_sequence.append(AIMessagePromptTemplate.from_template(msg["content"]))
            
            prompt_chain = ChatPromptTemplate.from_messages(prompt_sequence)
            processing_pipeline = prompt_chain | llm_engine | StrOutputParser()
            ai_response = processing_pipeline.invoke({})
        
        # Update message log and popup
        st.session_state.message_log.append({"role": "ai", "content": ai_response})
        st.session_state.popup["show"] = True
        st.session_state.popup["content"] = ai_response
        
        # Refresh the UI
        st.rerun()

if __name__ == '__main__':
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run Streamlit in the main thread
    run_streamlit()
