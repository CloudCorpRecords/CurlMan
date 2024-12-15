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
                    
                    # Security Score
                    score = request_info.get('security_score', {})
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Security Score", f"{score.get('score', 0)}/100")
                    with col2:
                        grade = score.get('grade', 'N/A')
                        st.metric("Security Grade", grade, 
                                delta="Good" if grade in ['A', 'B'] else "Needs Improvement")
                    
                    # URL Analysis
                    st.subheader("URL Analysis")
                    url_analysis = request_info['url_analysis']
                    cols = st.columns(2)
                    with cols[0]:
                        st.markdown(f"**Protocol:** {url_analysis['scheme']}")
                        st.markdown(f"**Host:** {url_analysis['host']}")
                        st.markdown(f"**Path:** {url_analysis['path']}")
                    with cols[1]:
                        st.markdown("**Security Status:**")
                        st.markdown("✅" if url_analysis['security']['uses_https'] else "⚠️" + " HTTPS")
                        if url_analysis['security']['has_sensitive_params']:
                            st.warning("⚠️ Sensitive data detected in URL parameters")
                    
                    # Authentication
                    st.subheader("Authentication")
                    auth_info = request_info['authentication']
                    if auth_info['present']:
                        st.success(f"✅ {auth_info['type']} (Security Level: {auth_info['security_level'].title()})")
                    else:
                        st.warning("⚠️ No authentication detected")
                    
                    # Headers Analysis
                    st.subheader("Headers Analysis")
                    headers_analysis = request_info['headers']['security_analysis']
                    
                    # Security Score
                    st.metric("Headers Security Score", f"{headers_analysis['security_score']}/100")
                    
                    # Security Headers
                    st.markdown("### Security Headers")
                    for header, info in headers_analysis['security_headers'].items():
                        with st.expander(f"{'✅' if info['present'] else '❌'} {header}"):
                            st.markdown(f"**Description:** {info['description']}")
                            if info['present']:
                                if 'valid' in info:
                                    st.markdown(f"**Valid Configuration:** {'✅' if info['valid'] else '❌'}")
                            else:
                                st.markdown(f"**Recommendation:** {info['recommendation']}")
                    
                    # Content Security
                    st.markdown("### Content Headers")
                    for header, info in headers_analysis['content_security'].items():
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**{header.title()}:** {'✅' if info['present'] else '❌'}")
                        with col2:
                            if info['present']:
                                st.markdown(f"Value: `{info['value']}`")
                    
                    # CORS Configuration
                    if headers_analysis['cors_configuration']['enabled']:
                        st.markdown("### CORS Configuration")
                        cors_headers = headers_analysis['cors_configuration']['headers']
                        for header, value in cors_headers.items():
                            if value:
                                st.markdown(f"**{header}:** `{value}`")
                    
                    # Cache Configuration
                    st.markdown("### Cache Configuration")
                    cache_info = headers_analysis['cache_configuration']
                    if cache_info['present']:
                        st.markdown(f"**Cache-Control:** `{cache_info['value']}`")
                        st.markdown("**Security Features:**")
                        st.markdown(f"- No Store: {'✅' if cache_info['no_store'] else '❌'}")
                        st.markdown(f"- Private: {'✅' if cache_info['private'] else '❌'}")
                    else:
                        st.warning(cache_info['recommendation'])
                    
                    # Request Body
                    if request_info.get('body', {}).get('present'):
                        st.subheader("Request Body")
                        body_info = request_info['body']
                        st.markdown(f"**Content Type:** {body_info['content_type']}")
                        st.markdown(f"**Size:** {body_info['size_bytes']} bytes")
                        if body_info['security_analysis']['contains_sensitive_data']:
                            st.warning("⚠️ Potentially sensitive data detected in request body")
                        if body_info['security_analysis']['size_warning']:
                            st.warning("⚠️ Large request body detected")
                    
                    # Security Recommendations
                    if score.get('recommendations'):
                        st.subheader("Security Recommendations")
                        for rec in score['recommendations']:
                            st.info(f"💡 {rec}")
                
                with tab2:
                    st.subheader("Response Details")
                    
                    # Response Overview
                    st.markdown("### 📊 Response Overview")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Status Code", response_info['status_code'])
                    with col2:
                        st.metric("Response Size", response_info['metadata']['size'])
                    with col3:
                        st.metric("Total Time", response_info['metadata']['timing']['total_time'])
                    
                    # Timing Metrics
                    st.markdown("### ⏱️ Timing Analysis")
                    timing_data = response_info['metadata']['timing']
                    timing_cols = st.columns(3)
                    with timing_cols[0]:
                        st.metric("DNS Lookup", timing_data.get('dns_lookup', 'N/A'))
                        st.metric("Connect Time", timing_data.get('connect_time', 'N/A'))
                    with timing_cols[1]:
                        st.metric("TLS Handshake", timing_data.get('tls_handshake', 'N/A'))
                        st.metric("Request Time", timing_data.get('request_time', 'N/A'))
                    with timing_cols[2]:
                        st.metric("Processing Time", timing_data.get('processing_time', 'N/A'))
                        st.metric("Server Time", timing_data.get('server_time', 'N/A'))
                    
                    # Performance Metrics
                    st.markdown("### 🚀 Performance Analysis")
                    perf_metrics = response_info['metadata']['performance_metrics']
                    
                    # Display various performance scores
                    score_cols = st.columns(4)
                    scores = perf_metrics.get('scores', {})
                    with score_cols[0]:
                        st.metric("Overall Score", f"{scores.get('total', 'N/A')}/100")
                    with score_cols[1]:
                        ttfb_score = scores.get('ttfb', 0)
                        st.metric("TTFB Score", f"{ttfb_score:.1f}/100" if isinstance(ttfb_score, (int, float)) else "N/A")
                    with score_cols[2]:
                        network_score = scores.get('network', 0)
                        st.metric("Network Score", f"{network_score:.1f}/100" if isinstance(network_score, (int, float)) else "N/A")
                    with score_cols[3]:
                        st.metric("Optimization Score", f"{scores.get('optimization', 'N/A')}/100")
                    
                    # Detailed Metrics
                    st.markdown("#### 📊 Detailed Metrics")
                    metric_cols = st.columns(3)
                    with metric_cols[0]:
                        st.markdown("**Time to First Byte:**")
                        st.markdown(f"`{perf_metrics['metrics']['ttfb']}`")
                        st.markdown("**Network Latency:**")
                        st.markdown(f"`{perf_metrics['metrics']['network_latency']}`")
                    with metric_cols[1]:
                        st.markdown("**DNS Resolution:**")
                        st.markdown(f"`{perf_metrics['metrics']['dns_time']}`")
                        if 'tls_time' in perf_metrics['metrics']:
                            st.markdown("**TLS Handshake:**")
                            st.markdown(f"`{perf_metrics['metrics']['tls_time']}`")
                    with metric_cols[2]:
                        st.markdown("**Response Features:**")
                        st.markdown("✅ Compression Enabled" if perf_metrics['compression_enabled'] else "❌ Compression Disabled")
                        st.markdown("✅ Connection Reused" if perf_metrics['connection_reused'] else "❌ New Connection")
                        st.markdown(f"📦 Size: {perf_metrics['response_size']}")
                    
                    # Performance Bottlenecks
                    if perf_metrics.get('bottlenecks'):
                        st.markdown("#### 🚨 Performance Bottlenecks")
                        for bottleneck in perf_metrics['bottlenecks']:
                            st.warning(bottleneck)
                    
                    # Performance Recommendations
                    if perf_metrics.get('recommendations'):
                        st.markdown("#### Performance Recommendations")
                        for rec in perf_metrics['recommendations']:
                            st.info(f"💡 {rec}")
                    
                    # Security Analysis
                    st.markdown("### 🔒 Security Analysis")
                    security = response_info['metadata']['security_analysis']
                    for header, info in security.items():
                        with st.expander(f"{'✅' if info['present'] else '❌'} {header}"):
                            st.markdown(f"**Description:** {info['description']}")
                            if info['present'] and 'value' in info:
                                st.code(info['value'])
                    
                    # Response Headers
                    st.markdown("### 📋 Response Headers")
                    with st.expander("View All Headers"):
                        for header, value in response_info['headers'].items():
                            st.markdown(f"**{header}:** {value}")
                    
                    # Response Content
                    st.markdown("### 📄 Response Content")
                    content_type = response_info.get('content_type', 'text/plain')
                    if 'application/json' in content_type:
                        st.json(response_info['content'])
                    else:
                        st.code(response_info['raw'], language='text')
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