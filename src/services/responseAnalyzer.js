import axios from 'axios';

export async function analyzeResponse(requestData) {
  try {
    const startTime = performance.now();
    
    // Execute request
    const response = await axios({
      method: requestData.method,
      url: requestData.url,
      headers: requestData.headers,
      data: requestData.data,
      validateStatus: () => true // Don't throw on any status code
    });

    const endTime = performance.now();
    const totalTime = endTime - startTime;

    // Analyze content type and prepare response
    const contentType = response.headers['content-type'] || '';
    let content = response.data;
    
    if (typeof content === 'object') {
      content = JSON.stringify(content, null, 2);
    }

    // Security headers check
    const securityHeaders = {
      'Strict-Transport-Security': {
        present: 'strict-transport-security' in response.headers,
        description: 'Enforces secure (HTTPS) connections to the server'
      },
      'X-Frame-Options': {
        present: 'x-frame-options' in response.headers,
        description: 'Protects against clickjacking attacks'
      },
      'X-Content-Type-Options': {
        present: 'x-content-type-options' in response.headers,
        description: 'Prevents MIME type sniffing'
      },
      'X-XSS-Protection': {
        present: 'x-xss-protection' in response.headers,
        description: 'Enables cross-site scripting filter in browsers'
      }
    };

    // Prepare response analysis
    const analysis = {
      status_code: response.status,
      reason: response.statusText,
      headers: response.headers,
      content_type: contentType,
      content: content,
      raw: typeof response.data === 'object' ? JSON.stringify(response.data) : response.data,
      metadata: {
        encoding: response.headers['content-encoding'] || 'identity',
        size: new Blob([response.data]).size,
        timing: {
          total_time: `${totalTime.toFixed(2)}ms`
        },
        redirect_count: response.request.res.responseUrl !== requestData.url ? 1 : 0,
        final_url: response.request.res.responseUrl,
        cookies: response.headers['set-cookie'] || [],
        security_analysis: securityHeaders
      }
    };

    return analysis;
  } catch (error) {
    throw new Error(`Request failed: ${error.message}`);
  }
}
