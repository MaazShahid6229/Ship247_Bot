import os
from typing import Literal

import streamlit as st
import tiktoken
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

from custom_tools import get_tools

# Load secrets from Streamlit
os.environ["AZURE_OPENAI_API_KEY"] = st.secrets["AZURE_OPENAI_API_KEY"]
azure_endpoint = st.secrets["AZURE_ENDPOINT"]
azure_deployment = st.secrets["AZURE_DEPLOYMENT"]
openai_api_version = st.secrets["OPENAI_API_VERSION"]

if not azure_endpoint:
    st.error("❌ API Key is missing! Please check your `secrets.toml` or environment variables.")
    st.stop()

# Initialize tokenizer for your model
encoding = tiktoken.get_encoding("cl100k_base")
MAX_TOKENS = 100000  # Set your model's max token limit here


def count_tokens(text: str) -> int:
    """Count the number of tokens in a message."""
    return len(encoding.encode(text))


def truncate_message(message: str, max_tokens: int) -> str:
    """Truncate message to fit within token limit."""
    tokens = encoding.encode(message)
    if len(tokens) > max_tokens:
        truncated_tokens = tokens[:max_tokens]
        return encoding.decode(truncated_tokens)
    return message


class ChatBot:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            azure_deployment=azure_deployment,
            openai_api_version=openai_api_version,
            streaming=True
        )

    def call_tool(self):
        tools = get_tools()
        self.tool_node = ToolNode(tools=tools)
        self.llm_with_tool = self.llm.bind_tools(tools)

    def call_model(self, state: MessagesState) -> dict:
        messages = state['messages']

        # Check total token count
        total_tokens = sum(count_tokens(message.content) for message in messages)

        if total_tokens > MAX_TOKENS:
            print(f"Total tokens: {total_tokens}, which exceeds the limit of {MAX_TOKENS}. Truncating messages.")
            # Truncate messages to fit within the token limit
            for i, message in enumerate(messages):
                messages[i].content = truncate_message(message.content, MAX_TOKENS)

        response = self.llm_with_tool.invoke(messages)
        return {"messages": [response]}

    def router_function(self, state: MessagesState) -> Literal["tools", END]:
        messages = state['messages']
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    def __call__(self):
        self.call_tool()
        workflow = StateGraph(MessagesState)
        workflow.add_node("agent", self.call_model)
        workflow.add_node("tools", self.tool_node)
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", self.router_function, {"tools": "tools", END: END})
        workflow.add_edge("tools", 'agent')
        self.app = workflow.compile()
        return self.app
