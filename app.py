import json

import requests
import streamlit as st

from bot import ChatBot

# API Endpoint
LOGIN_API_URL = "https://ship247.com/api/bot/login"

# Set up the Streamlit app UI
st.set_page_config(
    page_title="Ship247 ChatBot",
    page_icon=r"images/favicon.png",
    layout="centered"
)

# Open the file and load its contents into a dictionary
with open("apis.json", 'r') as json_file:
    data = json.load(json_file)

api_json = data["apis"]

# Initialize the chatbot and workflow
mybot = ChatBot()
workflow = mybot()

# Authentication Check
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Login Required")

    username = st.text_input("Enter your username:", key="username")
    password = st.text_input("Enter your password:", type="password")
    if st.button("Login"):
        if username and password:
            # Prepare payload for API request
            payload = {"email": username, "password": password}
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            # Make API request
            response = requests.post(LOGIN_API_URL, headers=headers, data=payload)

            # Handle response
            if response.status_code == 200:
                user_details = response.json()  # Store full user data
                if "status" not in user_details:
                    st.session_state.authenticated = True
                    st.session_state.user_data = user_details
                    st.session_state.messages = []
                    st.success("✅ Login successful! Redirecting...")
                    st.rerun()  # Refresh Streamlit app after login
                else:
                    st.error("❌ Login failed. Please check your credentials and try again.")
            else:
                st.error("❌ Login failed. Please check your credentials and try again.")
        else:
            st.warning("⚠️ Please enter both email and password.")

# If authenticated, show the chatbot
if st.session_state.authenticated:
    # Header Section with Logout Button
    col1, col2 = st.columns([0.7, 0.3])  # Creates two columns: 80% width and 20% width

    with col1:
        st.image(r"images/header_logo.svg", width=150)
        st.title("🤖 Ship247 ChatBot")

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Space for alignment

        # Show user name if available
        if st.session_state.user_data:
            user = st.session_state.user_data.get("user", {})
            full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            st.markdown(f"**👤 {full_name}**", unsafe_allow_html=True)  # Display name

        # Logout Button
        if st.button("🚪 Logout", key="logout_btn"):
            st.session_state.authenticated = False
            st.session_state.user_data = None  # Clear user session
            st.rerun()

        # Clear Chat Button
        if st.button("🗑️ Clear Chat", key="clear_chat_btn"):
            st.session_state.messages = []
            st.rerun()

    # Initialize session state for conversation history and loading state
    if "messages" not in st.session_state or st.session_state.messages == []:
        st.session_state.messages = [
            {"role": "system", "content": f"""
            You are an advanced logistics assistant for Ship247, helping users book and manage shipments via sea, land, and rail. Your job is to:
            - Provide shipping prices based on weight, volume, and transportation mode.
            - Show available schedules for shipments.
            - Track the status of a booking.
            - Process cancellations for existing bookings.
            - Recommend the best shipping method (cost vs. speed) when users provide weight and destination.

            Here is some API for Ship247:

            {api_json}

            Also you have here is user data: {st.session_state.user_data.get("user", {})} use this detail and provide the best service to the user. tell them user that you know the name and details of the user.
            use this token details for the API call: {st.session_state.user_data.get("token", {})}

            ### How You Work:
            1. **Understand the Query**
               - Identify whether the user needs pricing, scheduling, tracking, or cancellation.
               - If unclear, ask for clarification in a polite and concise way.

            2. **Validate Required Information**
               - Check if the user has provided all necessary details (e.g., weight, destination, transport mode).
               - If missing, request the info clearly:
                 - "To calculate your shipping price, please provide the destination and cargo weight."

            3. **Smart Shipping Recommendations**
               - If a user asks, "I have 20,000 kg cargo. What’s the best shipping option?", compare:
                 - Cost for sea, land, and rail.
                 - Transit time and delivery speed.
                 - Feasibility based on distance and cargo type.
               - Suggest the best option with a clear explanation:
                 - "For 20,000 kg, rail shipping is the cheapest at $500, arriving in 3 days."

            4. **Provide API-Based Responses**
               - Use available APIs to fetch real-time prices, schedules, and status updates.
               - Format the response in a structured, user-friendly manner.

            5. **Handle Edge Cases Gracefully**
               - If a booking cannot be canceled, explain why:
                 - "Your shipment is already in transit and cannot be canceled."
               - If a schedule is not available, suggest alternatives.

            6. **User-Friendly Output**
               - No raw JSON responses—use clear language and structured answers.
               - Example response for price inquiry:
                 "Shipping Options for 20,000 kg (Lahore to Dubai):
                  - 🚢 Sea Freight: $600, 7 days
                  - 🚆 Rail Freight: $500, 3 days
                  - 🚛 Land Freight: $750, 5 days
                  Recommended: Rail Freight for best cost & speed."

            ### Important Notes:
                - Make sure when calling a tool, you are passing the correct parameters. like headers and payload. and also the correct API name.

            contact details of Ship247 is:
                +97125469669
                info@ship247.com

            ### Tone & Style:
            - Professional yet friendly
            - Concise and direct
            - Actionable insights, not just raw data
            """
             }
        ]

    if "is_waiting" not in st.session_state:
        st.session_state.is_waiting = False

    # Display the conversation history dynamically
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # User input and bot response handling
    if not st.session_state.is_waiting:
        if user_input := st.chat_input("Ask me about Ship247"):
            st.chat_message("user").markdown(user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})

            st.session_state.is_waiting = True
            chatbot = ChatBot()
            workflow = chatbot()
            response = workflow.invoke({"messages": st.session_state.messages})

            bot_response = response["messages"][-1].content
            with st.chat_message("assistant"):
                st.markdown(bot_response)

            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            st.session_state.is_waiting = False

    # Footer
    st.markdown("---")
    st.caption("💬 Powered by Ship247")
