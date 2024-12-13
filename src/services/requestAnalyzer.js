export function analyzeRequest(requestData) {
  const url = new URL(requestData.url);
  
  const analysis = {
    method: requestData.method,
    url_analysis: {
      scheme: url.protocol.replace(':', ''),
      host: url.host,
      path: url.pathname,
      query_params: url.search,
      fragment: url.hash
    },
    headers: {
      count: Object.keys(requestData.headers).length,
      details: requestData.headers
    },
    authentication: {
      present: false,
      type: null
    }
  };

  // Analyze authentication
  const authHeaders = [
    ["Authorization", "Bearer", "Bearer Token"],
    ["Authorization", "Basic", "Basic Auth"],
    ["X-API-Key", null, "API Key"],
  ];

  for (const [header, prefix, authType] of authHeaders) {
    if (header in requestData.headers) {
      analysis.authentication.present = true;
      if (prefix && requestData.headers[header].startsWith(prefix)) {
        analysis.authentication.type = authType;
      } else if (!prefix) {
        analysis.authentication.type = authType;
      }
    }
  }

  // Analyze body if present
  if (requestData.data) {
    analysis.body = {
      present: true,
      size_bytes: new Blob([requestData.data]).size,
      content_preview: requestData.data.length > 200 
        ? requestData.data.substring(0, 200) + '...' 
        : requestData.data
    };
  } else {
    analysis.body = {
      present: false
    };
  }

  return analysis;
}
