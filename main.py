import streamlit as st
import time
from curl_parser import parse_curl_command
from request_analyzer import analyze_request
from response_analyzer import analyze_response
from utils import format_data, calculate_size

st.set_page_config(
    page_title="Curl Command Analyzer",
    page_icon="🔍",
    layout="wide"
)

def main():
    st.title("🔍 Curl Command Analyzer")
    st.markdown("""
    Enter a curl command to analyze its request and response details.
    The tool will provide comprehensive information about the API call.
    """)

    # Input area
    curl_command = st.text_area(
        "Enter curl command",
        height=100,
        placeholder="curl https://api.example.com/data -H 'Authorization: Bearer token'"
    )

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

                # Display results in tabs
                tab1, tab2, tab3 = st.tabs(["Request Details", "Response Details", "Raw Data"])

                with tab1:
                    st.subheader("Request Analysis")
                    st.json(request_info)

                with tab2:
                    st.subheader("Response Analysis")
                    
                    # Response metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Time", response_info['metadata']['timing']['total_time'])
                    with col2:
                        st.metric("Status Code", f"{response_info['status_code']} ({response_info['reason']})")
                    with col3:
                        st.metric("Response Size", response_info['metadata']['size'])
                    
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

        except Exception as e:
            st.error(f"Error analyzing curl command: {str(e)}")

if __name__ == "__main__":
    main()
