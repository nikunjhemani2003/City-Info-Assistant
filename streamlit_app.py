import streamlit as st
import asyncio
from main import RouterOutputAgentWorkflow, sql_tool, llama_cloud_tool
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Validate OpenAI API Key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    st.error("❌ OpenAI API Key is missing! Please check your .env file.")
    st.stop()

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! How can I assist you today?"}]

# Function to process queries asynchronously
async def process_query(query: str):
    """Process a query through the workflow."""
    try:
        wf = RouterOutputAgentWorkflow(tools=[sql_tool, llama_cloud_tool], verbose=True, timeout=120)
        result = await wf.run(message=query)
        return result
    except Exception as e:
        return f"Error: {str(e)}"

# Streamlit UI
st.set_page_config(page_title="City Info Assistant", page_icon="🏙️")

# Sidebar
with st.sidebar:
    st.title("Options")
    if st.button("Clear Chat"):
        st.session_state.messages = [{"role": "assistant", "content": "Hi! How can I assist you today?"}]
        st.experimental_rerun()

    st.markdown("---")
    st.markdown("### Available Tools:")
    st.markdown("- SQL Tool: Query city statistics.")
    st.markdown("- Llama Cloud Tool: Answer semantic questions about US cities.")

# Main interface
st.title("🏙️ City Information Assistant")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Query Input
if prompt := st.chat_input("Ask about cities:"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Show processing message
    with st.spinner("Processing your query..."):
        response = asyncio.run(process_query(prompt))

        # Display assistant response in chat message container
        st.chat_message("assistant").markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

