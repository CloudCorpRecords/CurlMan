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
                    st.metric("Response Time", f"{execution_time:.2f}ms")
                    st.metric("Status Code", response_info['status_code'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### Headers")
                        st.json(response_info['headers'])
                    with col2:
                        st.markdown("### Metadata")
                        st.json(response_info['metadata'])

                    if response_info['content']:
                        st.markdown("### Response Content")
                        st.code(format_data(
                            response_info['content'],
                            response_info['content_type']
                        ))

                with tab3:
                    st.subheader("Raw Response")
                    st.code(response_info['raw'])

        except Exception as e:
            st.error(f"Error analyzing curl command: {str(e)}")

if __name__ == "__main__":
    main()
