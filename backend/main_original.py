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

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize the chat engine
llm_engine = ChatOllama(
    model="deepseek-r1:1.5b",
    base_url="http://localhost:11434",
    temperature=0.3
)

# System prompt configuration
system_prompt = SystemMessagePromptTemplate.from_template(
    "You are an expert AI coding assistant. Provide concise, correct solutions "
    "with strategic print statements for debugging. Always respond in English. "
    "When providing code solutions: "
    "1. First explain the solution briefly "
    "2. Then show the code in a separate code block "
    "3. Finally add any necessary explanations about the code"
)

# Shared message history
message_history = []

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message')
        
        # Add user message to history
        message_history.append({"role": "user", "content": user_message})
        
        # Generate response using the shared LLM engine
        prompt_chain = ChatPromptTemplate.from_messages([
            system_prompt,
            *[HumanMessagePromptTemplate.from_template(msg["content"]) if msg["role"] == "user"
            else AIMessagePromptTemplate.from_template(msg["content"])
            for msg in message_history]
        ])
        processing_pipeline = prompt_chain | llm_engine | StrOutputParser()
        response = processing_pipeline.invoke({})
        
        # Add AI response to history
        message_history.append({"role": "ai", "content": response})
        
        return jsonify({
            'response': response
        })

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

def run_flask():
    app.run(port=5000)

def main():
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
            {"role": "ai", "content": "Hi! I'm DeepAssist. How can I help you code today? 💻"}
        ]

    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.message_log:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input for user queries
    user_query = st.chat_input("Type your coding question here....")

    # Handle user input
    if user_query:
        st.session_state.message_log.append({"role": "user", "content": user_query})
        
        # Generate AI response
        with st.spinner("Processing..."):
            prompt_chain = ChatPromptTemplate.from_messages([
                system_prompt,
                *[HumanMessagePromptTemplate.from_template(msg["content"]) if msg["role"] == "user"
                else AIMessagePromptTemplate.from_template(msg["content"])
                for msg in st.session_state.message_log]
            ])
            processing_pipeline = prompt_chain | llm_engine | StrOutputParser()
            ai_response = processing_pipeline.invoke({})

        # Append AI response to message log
        st.session_state.message_log.append({"role": "ai", "content": ai_response})
        st.rerun()

if __name__ == '__main__':
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run Streamlit in the main thread
    main()