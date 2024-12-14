import streamlit as st
import time
import json
from datetime import datetime
from curl_parser import parse_curl_command
from request_analyzer import analyze_request
from response_analyzer import analyze_response
from utils import format_data, calculate_size
from collections_manager import CollectionManager

st.set_page_config(
    page_title="Curl Command Analyzer",
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

def main():
    st.title("🔍 API Testing Studio")
    
    # Sidebar for collections and environments
    # Responsive sidebar width
    sidebar_width = 350 if st.session_state.get('expand_sidebar', True) else 200
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {{
            width: {sidebar_width}px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    with st.sidebar:
        # Add toggle for sidebar width
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header("📚 Collections")
        with col2:
            if st.button("↔️"):
                st.session_state.expand_sidebar = not st.session_state.get('expand_sidebar', True)
                st.rerun()
                
        collections = st.session_state.collection_manager.list_collections()
        selected_collection = st.selectbox(
            "Select Collection",
            [""] + collections,
            format_func=lambda x: "New Collection" if x == "" else x
        )
        
        if selected_collection == "":
            col1, col2 = st.columns([3, 1])
            with col1:
                new_collection_name = st.text_input("Collection Name")
            with col2:
                if st.button("Create") and new_collection_name:
                    st.session_state.collection_manager.create_collection(new_collection_name)
                    st.rerun()
        
        st.header("🔧 Environment")
        environments = list(st.session_state.collection_manager.environments.keys())
        st.session_state.selected_environment = st.selectbox(
            "Select Environment",
            environments,
            index=environments.index(st.session_state.selected_environment)
        )
        
        # Environment variables editor
        st.subheader("Environment Variables")
        env_vars = st.session_state.collection_manager.get_environment(st.session_state.selected_environment)
        
        with st.expander("About Environment Variables", expanded=False):
            st.markdown("""
            Use environment variables to store and reuse values across requests.
            Reference variables in your requests using `${VARIABLE_NAME}` syntax.
            
            Example:
            ```
            curl https://api.example.com/data -H 'Authorization: Bearer ${API_TOKEN}'
            ```
            """)
        
        # Organize variables by category
        categories = {
            "Authentication": ["token", "key", "secret", "auth", "api"],
            "URLs": ["url", "host", "endpoint", "domain"],
            "Other": []
        }
        
        categorized_vars = {cat: [] for cat in categories.keys()}
        for key in env_vars.keys():
            categorized = False
            for cat, patterns in categories.items():
                if any(pattern in key.lower() for pattern in patterns):
                    categorized_vars[cat].append(key)
                    categorized = True
                    break
            if not categorized:
                categorized_vars["Other"].append(key)
        
        # Compact Add Variable UI
        with st.expander("➕ Add New Variable", expanded=False):
            var_form = st.form("new_variable_form")
            new_var_col1, new_var_col2 = var_form.columns([1, 1])
            with new_var_col1:
                new_var_key = st.text_input("Variable Name", key="new_var_key")
                new_var_category = st.selectbox("Category", list(categories.keys()), key="new_var_cat")
            with new_var_col2:
                new_var_value = st.text_input("Value", type="password", key="new_var_value")
                submit_button = st.form_submit_button("Add Variable")
                
            if submit_button and new_var_key:
                st.session_state.collection_manager.set_environment_variable(
                    st.session_state.selected_environment,
                    new_var_key,
                    new_var_value
                )
                st.rerun()
        
        # Display variables by category
        for category, vars in categorized_vars.items():
            if vars:  # Only show categories with variables
                st.markdown(f"### {category}")
                for key in vars:
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    with col1:
                        st.text(key)
                    with col2:
                        value_hidden = st.text_input(
                            "Value",
                            value=env_vars[key],
                            type="password",
                            key=f"value_{key}",
                            label_visibility="collapsed"
                        )
                        if value_hidden != env_vars[key]:
                            st.session_state.collection_manager.set_environment_variable(
                                st.session_state.selected_environment,
                                key,
                                value_hidden
                            )
                    with col3:
                        if st.button("👁️", key=f"show_{key}"):
                            st.text(env_vars[key])
                    with col4:
                        if st.button("❌", key=f"delete_{key}"):
                            st.session_state.collection_manager.delete_environment_variable(
                                st.session_state.selected_environment,
                                key
                            )
                            st.rerun()
    
    # Main content area
    current_tab, history_tab = st.tabs(["New Request", "Request History"])
    
    with current_tab:
        st.markdown("""
        Enter a curl command to analyze its request and response details.
        The tool will provide comprehensive information about the API call.
        """)

    # Input area
    # Request input area
    input_col1, input_col2 = st.columns([3, 1])
    with input_col1:
        if selected_collection:
            # Get templates from collection
            collection = st.session_state.collection_manager.get_collection(selected_collection)
            if collection and collection.requests:
                templates = [req["name"] for req in collection.requests]
                selected_template = st.selectbox(
                    "Load from template",
                    [""] + templates,
                    format_func=lambda x: "New Request" if x == "" else x
                )
                if selected_template:
                    template_data = st.session_state.collection_manager.get_request_template(
                        selected_collection, selected_template
                    )
                    if template_data:
                        curl_command = template_data.get("curl_command", "")
                    else:
                        curl_command = ""
                else:
                    curl_command = ""
            else:
                curl_command = ""
        else:
            curl_command = ""
            
        curl_command = st.text_area(
            "Enter curl command",
            value=curl_command,
            height=100,
            placeholder="curl https://api.example.com/data -H 'Authorization: Bearer token'"
        )
    
    with input_col2:
        save_template = st.checkbox("Save as template")
        if save_template and selected_collection:
            template_name = st.text_input("Template name")
            template_desc = st.text_input("Description (optional)")

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
                start_time = time.time()
                response_info = analyze_response(parsed_request)
                execution_time = (time.time() - start_time) * 1000  # Convert to ms

                # Save to history
                save_to_history(curl_command, request_info, response_info)
                
                # Save as template if requested
                if save_template and selected_collection and template_name:
                    st.session_state.collection_manager.add_request_to_collection(
                        selected_collection,
                        {
                            "curl_command": curl_command,
                            "request_info": request_info,
                            "response_info": response_info
                        },
                        name=template_name,
                        description=template_desc
                    )
                    st.success(f"Saved template '{template_name}' to collection '{selected_collection}'")
                
                # Display results in tabs
                tab1, tab2, tab3, tab4, tab5 = st.tabs(["Request Details", "Response Details", "Raw Data", "Export Data", "AI Analysis"]) # Added a new tab

                with tab1:
                    st.subheader("Request Analysis")
                    st.json(request_info)
                    st.download_button(
                        "Download Request Analysis",
                        data=json.dumps(request_info, indent=2),
                        file_name="request_analysis.json",
                        mime="application/json"
                    )

                with tab2:
                    st.subheader("Response Analysis")
                    
                    from api_analyzer import analyze_api_health, get_optimization_suggestions
                    
                    # Response metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Time", response_info['metadata']['timing']['total_time'])
                    with col2:
                        st.metric("Status Code", f"{response_info['status_code']} ({response_info['reason']})")
                    with col3:
                        st.metric("Response Size", response_info['metadata']['size'])
                    
                    # API Health Analysis
                    st.markdown("### 🏥 API Health Analysis")
                    health_metrics = analyze_api_health(response_info)
                    
                    # Display health metrics with color-coded status
                    for category, info in health_metrics.items():
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            status_color = {
                                'good': '🟢',
                                'warning': '🟡',
                                'poor': '🔴',
                                'checking': '⚪'
                            }[info['status']]
                            st.markdown(f"### {status_color} {category.title()}")
                        with col2:
                            st.markdown(f"**Status**: {info['message']}")
                            if info['recommendations']:
                                st.markdown("**Recommendations:**")
                                for rec in info['recommendations']:
                                    st.markdown(f"- {rec}")
                    
                    # Optimization Suggestions
                    st.markdown("### 🚀 Optimization Suggestions")
                    suggestions = get_optimization_suggestions(request_info, response_info)
                    if suggestions:
                        for suggestion in suggestions:
                            st.info(suggestion)
                    else:
                        st.success("No immediate optimization suggestions - API appears to be well-optimized!")
                    
                    # Timing breakdown
                    st.markdown("### 📊 Timing Breakdown")
                    timing = response_info['metadata']['timing']
                    timing_cols = st.columns(4)
                    with timing_cols[0]:
                        st.metric("Session Setup", timing['session_setup'])
                    with timing_cols[1]:
                        st.metric("Request Time", timing['request_time'])
                    with timing_cols[2]:
                        st.metric("Processing Time", timing['processing_time'])
                    with timing_cols[3]:
                        st.metric("Server Time", timing['server_time'])
                    
                    # Headers and metadata
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### 📝 Headers")
                        st.json(response_info['headers'])
                    with col2:
                        st.markdown("### ℹ️ Metadata")
                        metadata_display = {
                            'encoding': response_info['metadata']['encoding'],
                            'redirect_count': response_info['metadata']['redirect_count'],
                            'final_url': response_info['metadata']['final_url'],
                            'cookies': response_info['metadata']['cookies']
                        }
                        st.json(metadata_display)
                    
                    # Security Analysis
                    st.markdown("### 🔒 Security Headers Analysis")
                    security = response_info['metadata']['security_analysis']
                    for header, info in security.items():
                        if info['present']:
                            st.success(f"✅ {header}: {info.get('value', '')}")
                            st.caption(info['description'])
                        else:
                            st.warning(f"⚠️ {header} not present - {info['description']}")
                    
                    # Add download button for response data
                    st.download_button(
                        "Download Complete Analysis",
                        data=json.dumps({
                            'request': request_info,
                            'response': response_info,
                            'timing': response_info['metadata']['timing'],
                            'security': response_info['metadata']['security_analysis']
                        }, indent=2),
                        file_name="complete_analysis.json",
                        mime="application/json"
                    )
                    
                    # Response Content
                    if response_info['content']:
                        st.markdown("### 📄 Response Content")
                        st.code(
                            format_data(
                                response_info['content'],
                                response_info['content_type']
                            ),
                            language="json" if "json" in response_info['content_type'] else "markup"
                        )

                with tab3:
                    st.subheader("Raw Response")
                    st.code(response_info['raw'])
                    st.download_button(
                        "Download Raw Response",
                        data=response_info['raw'],
                        file_name="raw_response.txt",
                        mime="text/plain"
                    )

                with tab4:
                    st.subheader("Export Data")
                    st.download_button(
                        "Download Request as JSON",
                        data=json.dumps(request_info, indent=2),
                        file_name='request_data.json',
                        mime='application/json'
                    )
                    st.download_button(
                        "Download Response as JSON",
                        data=json.dumps(response_info, indent=2),
                        file_name='response_data.json',
                        mime='application/json'
                    )
                    st.download_button(
                        "Download Raw Response as Text",
                        data=response_info['raw'],
                        file_name='raw_response.txt',
                        mime='text/plain'
                    )
                    st.download_button(
                        "Download All Data as JSON",
                        data=json.dumps({
                            'request': request_info,
                            'response': response_info,
                            'raw_response': response_info['raw']
                        }, indent=2),
                        file_name='all_data.json',
                        mime='application/json'
                    )


                with tab5: # AI Analysis Tab
                    st.subheader("🤖 AI-Powered API Analysis")

                    # Initialize chat state
                    if 'chat_messages' not in st.session_state:
                        st.session_state.chat_messages = []
                    if 'chat_manager' not in st.session_state:
                        from gemini_chat import GeminiChatManager
                        st.session_state.chat_manager = GeminiChatManager()

                    # Chat interface
                    st.markdown("#### Chat with AI Assistant")

                    # Display chat messages
                    for message in st.session_state.chat_messages:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])

                    # Initialize file state
                    if 'uploaded_files_data' not in st.session_state:
                        st.session_state.uploaded_files_data = []

                    # File uploader in a container
                    with st.container():
                        uploaded_files = st.file_uploader(
                            "Upload API-related files for analysis",
                            accept_multiple_files=True,
                            type=['py', 'json', 'yaml', 'txt'],
                            key='file_uploader'
                        )

                        # Process new uploads
                        if uploaded_files:
                            new_files = []
                            for file in uploaded_files:
                                content = file.read()
                                file.seek(0)  # Reset file pointer
                                new_files.append({
                                    'name': file.name,
                                    'content': content
                                })
                            st.session_state.uploaded_files_data = new_files

                    # Display uploaded files
                    if st.session_state.uploaded_files_data:
                        st.markdown("### 📎 Uploaded Files")
                        for file_data in st.session_state.uploaded_files_data:
                            st.markdown(f"- {file_data['name']}")

                    # Initialize analysis with current request/response
                    if st.button("Analyze Current API Call", key='analyze_button'):
                        with st.spinner("Analyzing API with AI..."):
                            try:
                                # Process all uploaded files
                                file_contents = []
                                for file_data in st.session_state.uploaded_files_data:
                                    processed = st.session_state.chat_manager.process_uploaded_file(
                                        file_data['content'],
                                        file_data['name']
                                    )
                                    file_contents.append(processed)

                                # Get AI analysis
                                ai_analysis = st.session_state.chat_manager.analyze_api(
                                    request_info,
                                    response_info,
                                    additional_context="\n\n".join(file_contents) if file_contents else None
                                )

                                # Add response to chat
                                st.session_state.chat_messages.append({
                                    "role": "assistant",
                                    "content": ai_analysis["analysis"]
                                })

                                # Provide optimized code download if available
                                if ai_analysis.get("files_path"):
                                    with open(ai_analysis["files_path"], "rb") as f:
                                        st.download_button(
                                            "Download Optimized API Implementation",
                                            f,
                                            file_name="optimized_api.zip",
                                            mime="application/zip",
                                            key='download_button'
                                        )
                            except Exception as e:
                                st.error(f"Error during AI analysis: {str(e)}")

                    # Chat input
                    if prompt := st.chat_input("Ask about API optimization..."):
                        # Add user message to chat
                        st.session_state.chat_messages.append({
                            "role": "user",
                            "content": prompt
                        })

                        # Process uploaded files
                        file_contents = []
                        if uploaded_files:
                            for file in uploaded_files:
                                file_contents.append(
                                    st.session_state.chat_manager.process_uploaded_file(
                                        file.read(),
                                        file.name
                                    )
                                )

                        # Get AI response
                        with st.spinner("AI is thinking..."):
                            try:
                                response = st.session_state.chat_manager.analyze_api(
                                    request_info,
                                    response_info,
                                    additional_context="\n\n".join(file_contents) if file_contents else None,
                                    user_prompt=prompt
                                )

                                # Add AI response to chat
                                st.session_state.chat_messages.append({
                                    "role": "assistant",
                                    "content": response["analysis"]
                                })

                                # Provide optimized code download if available
                                if response.get("files_path"):
                                    with open(response["files_path"], "rb") as f:
                                        st.download_button(
                                            "Download Optimized API Implementation",
                                            f,
                                            file_name="optimized_api.zip",
                                            mime="application/zip"
                                        )
                            except Exception as e:
                                st.error(f"Error getting AI response: {str(e)}")
                                st.session_state.chat_messages.append({
                                    "role": "assistant",
                                    "content": f"Sorry, I encountered an error: {str(e)}"
                                })


        except Exception as e:
            st.error(f"Error analyzing curl command: {str(e)}")
    
    with history_tab:
        st.subheader("📜 Request History")
        if not st.session_state.request_history:
            st.info("No requests have been made yet. Your request history will appear here.")
        else:
            # Add history controls
            col1, col2 = st.columns([3, 1])
            with col1:
                search = st.text_input("🔍 Filter history", placeholder="Search by endpoint, status code, or method...")
            with col2:
                if st.button("Export History", key="export"):
                    st.download_button(
                        "Download JSON",
                        data=json.dumps(st.session_state.request_history, indent=2),
                        file_name="curl_history.json",
                        mime="application/json"
                    )
            
            # Initialize comparison mode if not exists
            if 'compare_mode' not in st.session_state:
                st.session_state.compare_mode = False
                st.session_state.compare_selections = []
            
            # Add comparison toggle
            st.session_state.compare_mode = st.checkbox(
                "Enable Comparison Mode",
                value=st.session_state.compare_mode,
                help="Select two requests to compare their details"
            )
            
            filtered_history = st.session_state.request_history
            if search:
                filtered_history = [
                    entry for entry in st.session_state.request_history
                    if (search.lower() in entry['endpoint'].lower() or
                        search in str(entry['status_code']) or
                        search.lower() in entry['method'].lower())
                ]
            
            for i, entry in enumerate(filtered_history):
                success_icon = "✅" if entry['success'] else "❌"
                with st.expander(
                    f"{success_icon} [{entry['method']}] {entry['endpoint']} - {entry['timestamp']} ({entry['status_code']})"
                ):
                    st.text("Curl Command:")
                    st.code(entry['curl_command'])
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Status Code", entry['status_code'])
                    with col2:
                        st.metric("Execution Time", entry['execution_time'])
                    with col3:
                        if st.button("Rerun Request", key=f"rerun_{i}"):
                            st.session_state.rerun_command = entry['curl_command']
                            st.rerun()
                    with col4:
                        if st.session_state.compare_mode:
                            if st.button("Select for Comparison", key=f"compare_{i}"):
                                if entry['id'] not in st.session_state.compare_selections:
                                    st.session_state.compare_selections.append(entry['id'])
                                    if len(st.session_state.compare_selections) > 2:
                                        st.session_state.compare_selections.pop(0)
                                    st.rerun()
                    
                    # Show comparison if two items are selected
                    if (st.session_state.compare_mode and 
                        len(st.session_state.compare_selections) == 2 and 
                        entry['id'] in st.session_state.compare_selections):
                        st.markdown("### 📊 Comparison View")
                        other_id = [id for id in st.session_state.compare_selections if id != entry['id']][0]
                        other_entry = next(e for e in st.session_state.request_history if e['id'] == other_id)
                        
                        # Compact comparison metrics with better responsive layout
                        st.markdown("### Request Comparison")
                        metrics_container = st.container()
                        with metrics_container:
                            metric_cols = st.columns(6)
                            
                            # Request A metrics
                            with metric_cols[0]:
                                st.markdown(f"**A (ID: {entry['id']})**")
                            with metric_cols[1]:
                                st.metric("Status", entry['status_code'])
                            with metric_cols[2]:
                                st.metric("Time", f"{entry['execution_time']:.0f}ms")
                                
                            # Request B metrics
                            with metric_cols[3]:
                                st.markdown(f"**B (ID: {other_id})**")
                            with metric_cols[4]:
                                st.metric("Status", other_entry['status_code'])
                            with metric_cols[5]:
                                st.metric("Time", f"{other_entry['execution_time']:.0f}ms")
                        
                        # Response comparison
                        st.markdown("### Response Comparison")
                        compare_tabs = st.tabs(["Headers", "Response Body", "Timing"])
                        
                        with compare_tabs[0]:
                            headers_col1, headers_col2 = st.columns(2)
                            with headers_col1:
                                st.markdown("**Request A Headers**")
                                st.json(entry['request_info']['headers'])
                            with headers_col2:
                                st.markdown("**Request B Headers**")
                                st.json(other_entry['request_info']['headers'])
                        
                        with compare_tabs[1]:
                            body_col1, body_col2 = st.columns(2)
                            with body_col1:
                                st.markdown("**Request A Response**")
                                st.json(entry['response_info'].get('content', {}))
                            with body_col2:
                                st.markdown("**Request B Response**")
                                st.json(other_entry['response_info'].get('content', {}))
                        
                        with compare_tabs[2]:
                            timing_col1, timing_col2 = st.columns(2)
                            with timing_col1:
                                st.markdown("**Request A Timing**")
                                st.json(entry['response_info']['metadata']['timing'])
                            with timing_col2:
                                st.markdown("**Request B Timing**")
                                st.json(other_entry['response_info']['metadata']['timing'])
                    
                    tabs = st.tabs(["Request Info", "Response Info", "Analysis"])
                    with tabs[0]:
                        st.json(entry['request_info'])
                    with tabs[1]:
                        st.json(entry['response_info'])
                    with tabs[2]:
                        from api_analyzer import analyze_api_health, get_optimization_suggestions
                        health_metrics = analyze_api_health(entry['response_info'])
                        suggestions = get_optimization_suggestions(entry['request_info'], entry['response_info'])
                        
                        st.markdown("#### 🏥 Health Metrics")
                        for category, info in health_metrics.items():
                            st.markdown(f"**{category}**: {info['status']} - {info['message']}")
                        
                        st.markdown("#### 🚀 Optimization Suggestions")
                        for suggestion in suggestions:
                            st.info(suggestion)

if __name__ == "__main__":
    main()