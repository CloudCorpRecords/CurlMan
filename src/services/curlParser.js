const URL_REGEX = /^(http|https):\/\/[^ "]+$/;

export function parseCurlCommand(curlCommand) {
  // Remove newlines and extra spaces
  curlCommand = curlCommand.trim().replace(/\s+/g, ' ');
  
  try {
    // Split the command respecting quoted strings
    const parts = curlCommand.match(/(?:[^\s"']+|"[^"]*"|'[^']*')+/g);
    
    if (!parts || !parts[0].toLowerCase() === 'curl') {
      throw new Error("Command must start with 'curl'");
    }

    const requestData = {
      method: 'GET',  // Default method
      url: '',
      headers: {},
      data: null,
      params: {},
    };

    for (let i = 1; i < parts.length; i++) {
      const part = parts[i];
      
      // Handle URL (if not a flag)
      if (!part.startsWith('-')) {
        requestData.url = part.replace(/["']/g, '');
        continue;
      }

      // Handle flags
      switch (part) {
        case '-H':
        case '--header':
          if (i + 1 >= parts.length) {
            throw new Error(`Missing value for ${part}`);
          }
          const headerLine = parts[++i].replace(/["']/g, '');
          const [key, ...value] = headerLine.split(':');
          requestData.headers[key.trim()] = value.join(':').trim();
          break;

        case '-X':
        case '--request':
          if (i + 1 >= parts.length) {
            throw new Error(`Missing value for ${part}`);
          }
          requestData.method = parts[++i].toUpperCase();
          break;

        case '-d':
        case '--data':
        case '--data-raw':
          if (i + 1 >= parts.length) {
            throw new Error(`Missing value for ${part}`);
          }
          requestData.data = parts[++i].replace(/["']/g, '');
          if (requestData.method === 'GET') {
            requestData.method = 'POST';
          }
          break;

        default:
          // Skip unknown flags
          break;
      }
    }

    // Validate URL
    if (!requestData.url) {
      throw new Error('No URL specified in curl command');
    }
    
    if (!URL_REGEX.test(requestData.url)) {
      throw new Error('Invalid URL format');
    }

    return requestData;
  } catch (error) {
    throw new Error(`Error parsing curl command: ${error.message}`);
  }
}
