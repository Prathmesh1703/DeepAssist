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

app = Flask(__name__)
CORS(app)

# Initialize the chat engine
llm_engine = ChatOllama(
    model="deepseek-r1:1.5b",
    base_url="http://localhost:11434",
    temperature=0.3
)

# System prompt configuration - Updated to match main.py
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
message_history = []

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message')
        
        # Add user message to history
        message_history.append({"role": "user", "content": user_message})
        
        # Build prompt chain
        prompt_sequence = [system_prompt]
        for msg in message_history:
            if msg["role"] == "user":
                prompt_sequence.append(HumanMessagePromptTemplate.from_template(msg["content"]))
            elif msg["role"] == "ai":
                prompt_sequence.append(AIMessagePromptTemplate.from_template(msg["content"]))
        
        prompt_chain = ChatPromptTemplate.from_messages(prompt_sequence)
        
        # Generate response
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

if __name__ == '__main__':
    app.run(port=5000)