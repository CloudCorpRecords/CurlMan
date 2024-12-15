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
                    # Response Details
                    st.subheader("Response Details")
                    
                    # Response Overview with Enhanced Metrics
                    st.markdown("### 📊 Response Overview")
                    overview_cols = st.columns(4)
                    with overview_cols[0]:
                        status_color = "🟢" if 200 <= response_info['status_code'] < 300 else "🟡" if response_info['status_code'] < 500 else "🔴"
                        st.metric("Status Code", f"{status_color} {response_info['status_code']}")
                    with overview_cols[1]:
                        st.metric("Response Size", response_info['metadata']['size'])
                    with overview_cols[2]:
                        total_time = float(response_info['metadata']['timing']['total_time'].replace('ms', ''))
                        time_indicator = "🟢" if total_time < 500 else "🟡" if total_time < 1000 else "🔴"
                        st.metric("Total Time", f"{time_indicator} {response_info['metadata']['timing']['total_time']}")
                    with overview_cols[3]:
                        st.metric("Content Encoding", response_info['metadata'].get('encoding', 'None'))
                    
                    # Detailed Timing Analysis
                    st.markdown("### ⏱️ Response Timeline")
                    timing_data = response_info['metadata']['timing']
                    
                    # Create a timeline visualization
                    timeline_data = {
                        "DNS Lookup": float(timing_data.get('dns_lookup', '0ms').replace('ms', '')),
                        "TCP Connect": float(timing_data.get('connect_time', '0ms').replace('ms', '')),
                        "TLS Handshake": float(timing_data.get('tls_handshake', '0ms').replace('ms', '')) if timing_data.get('tls_handshake') else 0,
                        "Server Processing": float(timing_data.get('processing_time', '0ms').replace('ms', '')),
                        "Content Transfer": float(timing_data.get('request_time', '0ms').replace('ms', ''))
                    }
                    
                    # Display timeline metrics with performance indicators
                    timeline_cols = st.columns(len(timeline_data))
                    for idx, (phase, time) in enumerate(timeline_data.items()):
                        with timeline_cols[idx]:
                            indicator = "🟢" if time < 100 else "🟡" if time < 300 else "🔴"
                            st.metric(
                                phase,
                                f"{indicator} {time:.1f}ms",
                                help=f"Target: <100ms 🟢, <300ms 🟡, >300ms 🔴"
                            )
                    
                    # Detailed Server Timing
                    if 'server_time' in timing_data:
                        st.markdown("#### 🖥️ Server-side Timing")
                        server_time = str(timing_data['server_time'])
                        st.info(f"Server processing time: {server_time}")
                    
                    # Enhanced Performance Metrics
                    st.markdown("### 🚀 Performance Analysis")
                    perf_metrics = response_info['metadata']['performance_metrics']
                    
                    # Performance Score with detailed breakdown
                    score_cols = st.columns([2, 3])
                    with score_cols[0]:
                        score = perf_metrics['total_score']
                        score_color = "🟢" if score >= 90 else "🟡" if score >= 70 else "🔴"
                        st.metric(
                            "Performance Score",
                            f"{score_color} {score}/100",
                            help="90+ 🟢 Excellent, 70-89 🟡 Good, <70 🔴 Needs Improvement"
                        )
                    with score_cols[1]:
                        st.markdown("#### Score Breakdown")
                        st.progress(score/100)
                        st.caption(f"Based on response time, compression, caching, and optimization metrics")
                    
                    # Detailed Performance Metrics
                    st.markdown("#### Key Performance Indicators")
                    perf_cols = st.columns(4)
                    
                    with perf_cols[0]:
                        compression_status = "✅ Enabled" if perf_metrics['compression_enabled'] else "❌ Disabled"
                        st.metric(
                            "Compression",
                            compression_status,
                            delta="Optimal" if perf_metrics['compression_enabled'] else "Improvement needed",
                            delta_color="normal" if perf_metrics['compression_enabled'] else "inverse"
                        )
                        
                    with perf_cols[1]:
                        connection_status = "✅ Reused" if perf_metrics['connection_reused'] else "❌ New Connection"
                        st.metric(
                            "Connection",
                            connection_status,
                            delta="Optimal" if perf_metrics['connection_reused'] else "Could be improved",
                            delta_color="normal" if perf_metrics['connection_reused'] else "inverse"
                        )
                        
                    with perf_cols[2]:
                        size = perf_metrics['response_size']
                        size_status = "🟢" if 'KB' in size and float(size.split()[0]) < 500 else "🟡" if 'KB' in size else "🔴"
                        st.metric(
                            "Response Size",
                            f"{size_status} {size}",
                            help="🟢 <500KB, 🟡 500KB-1MB, 🔴 >1MB"
                        )
                        
                    with perf_cols[3]:
                        cache_status = "✅" if response_info['headers'].get('cache-control') else "❌"
                        st.metric(
                            "Caching",
                            f"{cache_status} {'Configured' if cache_status == '✅' else 'Not Configured'}",
                            delta="Optimal" if cache_status == '✅' else "Add caching",
                            delta_color="normal" if cache_status == '✅' else "inverse"
                        )
                    
                    # Performance Recommendations with Explanations
                    if perf_metrics.get('recommendations'):
                        st.markdown("#### 💡 Performance Optimization Suggestions")
                        for idx, rec in enumerate(perf_metrics['recommendations'], 1):
                            with st.expander(f"Recommendation {idx}"):
                                st.markdown(f"**{rec}**")
                                # Add specific guidance based on the recommendation
                                if "caching" in rec.lower():
                                    st.info("Implement cache headers with appropriate max-age values to reduce server load")
                                elif "compression" in rec.lower():
                                    st.info("Enable gzip or Brotli compression to reduce transfer sizes")
                                elif "connection" in rec.lower():
                                    st.info("Use keep-alive connections to reduce connection overhead")
                    
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
    
    # Feedback Form in Sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("📝 Give Feedback", use_container_width=True):
        st.session_state.show_feedback = True
    
    # Show feedback form
    if st.session_state.get('show_feedback', False):
        with st.sidebar.form("feedback_form"):
            st.write("### Share Your Feedback")
            category = st.selectbox(
                "Feedback Type",
                ["Bug Report", "Feature Request", "General Feedback"]
            )
            description = st.text_area("Your Feedback")
            email = st.text_input("Email (optional)", key="feedback_email")
            
            if st.form_submit_button("Submit Feedback"):
                try:
                    import json
                    from datetime import datetime
                    import uuid
                    import os
                    
                    feedback_entry = {
                        "id": str(uuid.uuid4()),
                        "timestamp": datetime.now().isoformat(),
                        "category": category.lower().replace(" ", "_"),
                        "description": description,
                        "environment": {
                            "browser": "Web Browser",
                            "app_version": "1.0.0"
                        },
                        "contact": {"email": email} if email else {},
                        "status": "new"
                    }
                    
                    # Create feedback directory if it doesn't exist
                    os.makedirs("feedback", exist_ok=True)
                    
                    # Load existing feedback
                    feedback_file = "feedback/feedback_data.json"
                    try:
                        with open(feedback_file, 'r') as f:
                            feedback_data = json.load(f)
                    except (FileNotFoundError, json.JSONDecodeError):
                        feedback_data = {"feedback_entries": []}
                    
                    # Add new feedback
                    feedback_data["feedback_entries"].append(feedback_entry)
                    
                    # Save updated feedback
                    with open(feedback_file, 'w') as f:
                        json.dump(feedback_data, f, indent=2)
                    
                    st.sidebar.success("Thank you for your feedback!")
                    st.session_state.show_feedback = False
                except Exception as e:
                    st.sidebar.error(f"Error saving feedback: {str(e)}")
    
    # Main navigation
    st.sidebar.markdown("---")
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