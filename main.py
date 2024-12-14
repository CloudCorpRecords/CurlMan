import streamlit as st
import time
import json
import asyncio
from datetime import datetime
from curl_parser import parse_curl_command
from request_analyzer import analyze_request
from response_analyzer import analyze_response
from utils import format_data, calculate_size
from collections_manager import CollectionManager

st.set_page_config(
    page_title="API Testing Studio",
    page_icon="🔍",
    layout="wide"
)

# Initialize session states
if 'request_history' not in st.session_state:
    st.session_state.request_history = []

# Initialize collection manager
if 'collection_manager' not in st.session_state:
    st.session_state.collection_manager = CollectionManager()

# Initialize selected environment
if 'selected_environment' not in st.session_state:
    st.session_state.selected_environment = "default"

def save_to_history(curl_command, request_info, response_info):
    """Save the request and response information to history with enhanced metadata."""
    history_entry = {
        'id': len(st.session_state.request_history),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'curl_command': curl_command,
        'request_info': request_info,
        'response_info': response_info,
        'status_code': response_info['status_code'],
        'execution_time': response_info['metadata']['timing']['total_time'],
        'success': 200 <= response_info['status_code'] < 300,
        'endpoint': request_info['url_analysis']['path'],
        'method': request_info['method'],
        'tags': []  # For future use - allowing users to tag requests
    }
    st.session_state.request_history.insert(0, history_entry)  # Add to beginning of list
    
    # Keep only the last 50 requests to manage memory
    if len(st.session_state.request_history) > 50:
        st.session_state.request_history = st.session_state.request_history[:50]

def websocket_testing_view():
    """WebSocket Testing View"""
    st.header("🔌 WebSocket Testing")
    
    # Initialize WebSocket handler if not exists
    if 'websocket_handler' not in st.session_state:
        from websocket_handler import WebSocketHandler
        st.session_state.websocket_handler = WebSocketHandler()

    # Connection Configuration
    st.subheader("WebSocket Connection")
    
    ws_url = st.text_input(
        "WebSocket URL",
        placeholder="ws://example.com/websocket",
        help="Enter the WebSocket URL (ws:// or wss://)"
    )
    
    # Headers Configuration
    with st.expander("Headers (Optional)", expanded=False):
        header_list = []
        for i in range(5):  # Allow up to 5 headers
            col1, col2 = st.columns(2)
            with col1:
                key = st.text_input(f"Header Key {i+1}", key=f"ws_header_key_{i}")
            with col2:
                value = st.text_input(f"Header Value {i+1}", key=f"ws_header_val_{i}")
            if key and value:
                header_list.append((key, value))
    
    # Connection Controls and Status
    status_col, control_col1, control_col2 = st.columns([1, 1, 1])
    
    with status_col:
        connection_info = st.session_state.websocket_handler.get_connection_info()
        if connection_info['is_connected']:
            st.success(f"Connected to {connection_info['url']}")
        elif 'error' in connection_info:
            st.error(f"Connection error: {connection_info['error']}")
        else:
            st.info("Not connected")
    
    with control_col1:
        if st.button("Connect", disabled=not ws_url or connection_info['is_connected']):
            headers = dict(header_list) if header_list else None
            try:
                async def connect():
                    return await st.session_state.websocket_handler.connect(ws_url, headers)
                success = asyncio.run(connect())
                if success:
                    st.success("Connected successfully!")
                    st.experimental_rerun()
            except Exception as e:
                st.error(f"Connection failed: {str(e)}")
    
    with control_col2:
        if st.button("Disconnect", disabled=not connection_info['is_connected']):
            try:
                async def disconnect():
                    await st.session_state.websocket_handler.disconnect()
                asyncio.run(disconnect())
                st.success("Disconnected successfully!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Disconnect failed: {str(e)}")
    
    # Message Sending
    st.subheader("Send Message")
    message = st.text_area("Message Content", placeholder="Enter your message here")
    if st.button("Send", disabled=not message or not st.session_state.websocket_handler.is_connected):
        async def send_message():
            return await st.session_state.websocket_handler.send_message(message)
        success = asyncio.run(send_message())
        if success:
            st.success("Message sent successfully!")
        else:
            st.error("Failed to send message. Check connection.")
    
    # Message History
    st.subheader("Message History")
    if st.button("Clear History"):
        st.session_state.websocket_handler.clear_message_history()
        st.rerun()
    
    messages = st.session_state.websocket_handler.get_message_history()
    if not messages:
        st.info("No messages yet. Connect to a WebSocket server and start sending messages!")
    else:
        for msg in messages:
            direction = "➡️" if msg['direction'] == 'sent' else "⬅️"
            with st.container():
                st.markdown(f"**{direction} {msg['timestamp']}**")
                st.code(msg['content'], language="json")

def graphql_view():
    """GraphQL View"""
    st.header("🔮 GraphQL Query Builder")
    
    if 'graphql_analyzer' not in st.session_state:
        from graphql_handler import GraphQLAnalyzer
        st.session_state.graphql_analyzer = GraphQLAnalyzer()

    # Query Building Section
    st.subheader("Build Query")
    
    operation_type = st.selectbox(
        "Operation Type",
        ["query", "mutation"],
        key="operation_type"
    )
    
    operation_name = st.text_input(
        "Operation Name (Optional)",
        placeholder="MyQuery",
        key="operation_name"
    )
    
    # Query Editor
    query = st.text_area(
        "GraphQL Query",
        placeholder="""query {
  viewer {
    name
    email
  }
}""",
        height=200,
        key="graphql_query"
    )
    
    # Variables Editor
    with st.expander("Query Variables (Optional)"):
        variables = st.text_area(
            "Variables (JSON format)",
            placeholder="""{"id": "123"}""",
            height=100,
            key="graphql_variables"
        )

    endpoint = st.text_input(
        "GraphQL Endpoint",
        placeholder="https://api.example.com/graphql",
        key="graphql_endpoint"
    )

    if st.button("Execute Query", type="primary"):
        try:
            variables_dict = json.loads(variables) if variables else {}
            request = st.session_state.graphql_analyzer.format_request({
                "query": query,
                "variables": variables_dict,
                "operation_name": operation_name if operation_name else None
            })
            
            # Execute and analyze the request
            response_info = analyze_response(request)
            request_info = analyze_request(request)
            
            # Save to history
            save_to_history(f"GraphQL Query: {operation_name or 'Unnamed'}", request_info, response_info)
            
            # Display results
            st.success("Query executed successfully!")
            
            # Show response data
            st.subheader("Response")
            st.json(response_info.get("content", {}))
            
        except Exception as e:
            st.error(f"Error executing query: {str(e)}")

def collections_view():
    """Collections View"""
    st.header("📚 Collections")
    st.markdown("Manage your API collections and templates here.")
    
    # Collections management UI will be implemented here
    st.info("Collections management interface coming soon!")

def analyze_request_view():
    """Request Analyzer View"""
    st.subheader("🔍 API Request Analysis")
    st.markdown("""
    Enter a curl command to analyze its request and response details.
    The tool will provide comprehensive information about the API call.
    """)

    # Request input area
    input_col1, input_col2 = st.columns([3, 1])
    with input_col1:
        curl_command = st.text_area(
            "Enter curl command",
            height=100,
            placeholder="curl https://api.example.com/data -H 'Authorization: Bearer token'"
        )
    
    with input_col2:
        save_template = st.checkbox("Save as template")

    if st.button("Analyze", type="primary"):
        if not curl_command:
            st.error("Please enter a curl command")
            return

        try:
            with st.spinner("Analyzing curl command..."):
                # Parse curl command
                parsed_request = parse_curl_command(curl_command)
                
                # Analyze request
                request_info = analyze_request(parsed_request)
                
                # Execute request and analyze response
                response_info = analyze_response(parsed_request)
                
                # Save to history
                save_to_history(curl_command, request_info, response_info)
                
                # Display results in tabs
                tab1, tab2 = st.tabs(["Request Details", "Response Details"])
                
                with tab1:
                    st.subheader("Request Analysis")
                    st.json(request_info)
                
                with tab2:
                    st.subheader("Response Details")
                    st.json(response_info)
        except Exception as e:
            st.error(f"Error analyzing request: {str(e)}")

def main():
    st.title("🔍 API Testing Studio")
    
    # Main navigation
    nav_options = {
        "🔍 Request Analyzer": "analyzer",
        "📚 Collections": "collections",
        "🔌 WebSocket Testing": "websocket",
        "🔮 GraphQL": "graphql"
    }
    
    selected_page = st.sidebar.radio("Navigation", list(nav_options.keys()))
    current_view = nav_options[selected_page]

    # Content based on navigation selection
    if current_view == "analyzer":
        analyze_request_view()
    elif current_view == "websocket":
        websocket_testing_view()
    elif current_view == "graphql":
        graphql_view()
    elif current_view == "collections":
        collections_view()

if __name__ == "__main__":
    main()