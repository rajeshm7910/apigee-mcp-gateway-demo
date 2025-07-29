# Apigee SSE Demo

A real-time chat interface that demonstrates Server-Sent Events (SSE) streaming with Apigee API Gateway. This demo showcases how to build a streaming chat application that connects to an Apigee proxy for real-time AI responses.

## Features

- Real-time streaming chat interface
- Server-Sent Events (SSE) integration with Apigee
- API key authentication support
- Modern, responsive UI with typing indicators
- Easy deployment and configuration

## Prerequisites

- Node.js and npm installed
- Apigee X account with API proxy deployment access
- API proxy bundle (included in `resources/apigee-sse-demo.zip`)

## Setup Instructions

### 1. Upload API Proxy Bundle

1. Log into your Apigee Edge/Cloud console
2. Navigate to **APIs** → **API Proxies**
3. Click **+ Proxy** and select **Upload Proxy Bundle**
4. Upload the `resources/apigee-sse-demo.zip` file
5. Name your proxy (e.g., `apigee-sse-demo`)
6. Click **Upload**

### 2. Configure Target Server

1. In your Apigee console, go to **Admin** → **Environments** → **Target Servers**
2. Update the Target server default.xml:
   - **key**: `Gemini API Key`
3. Save the target server configuration

### 3. Deploy the API Proxy

1. Go to your newly created API proxy
2. Click **Deploy** in the top right corner
3. Select your environment (e.g., `test` or `prod`)
4. Click **Deploy**
5. Note the deployment URL (e.g., `https://your-org-test.apigee.net/apigee-sse-demo`)

### 4. Update Configuration

Edit `index.html` and update the following configuration:

```javascript
// Find this line in the JavaScript section (around line 130)
let url = 'https://bap-amer-west-demo1.cs.apigee.net/apigee-sse-demo';

// Replace with your deployed proxy URL
let url = 'https://your-org-test.apigee.net/apigee-sse-demo';
```

**Optional**: If your proxy requires an API key, users can enter it in the API Key field in the UI.

### 5. Install Dependencies

```bash
npm install
```

This will install the required `http-server` dependency for serving the static files.

### 6. Start the Application

```bash
npm start
```

The application will start on `http://localhost:5200`

### 7. Access the Chat Interface

1. Open your web browser
2. Navigate to `http://localhost:5200`
3. You'll see the chat interface with:
   - API Key input field (optional)
   - Message input field
   - Send button

## Usage

### Basic Chat

1. Type your message in the input field
2. Click **Send** or press **Enter**
3. Watch the real-time streaming response from the AI
4. The response will appear with a typing indicator and stream in real-time

### With API Key Authentication

1. Enter your API key in the "API Key" field at the top
2. The key will be automatically included in all requests
3. This is useful if your Apigee proxy requires authentication

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser  │───▶│  Apigee Proxy   │───▶│  Gemini API     │
│   (index.html) │    │  (SSE Gateway)  │    │  (AI Service)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

- **Frontend**: Static HTML/JavaScript chat interface
- **Apigee Proxy**: Handles authentication, rate limiting, and SSE streaming
- **Backend**: AI service that generates streaming responses

## Configuration Details

### API Proxy Configuration

The proxy bundle includes:
- **Target Server**: Points to your backend AI service
- **SSE Policies**: Handles Server-Sent Events streaming
- **Authentication**: Optional API key validation
- **CORS**: Cross-origin resource sharing for web access

### Frontend Configuration

Key configuration points in `index.html`:

```javascript
// API endpoint URL
let url = 'https://your-org-test.apigee.net/apigee-sse-demo';

// Request headers
headers: {
  'Content-Type': 'application/json',
  'Accept': 'text/event-stream',
}

// Request body format
body: JSON.stringify({
  contents: [
    { parts: [ { text: userMessage } ] }
  ]
})
```

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure your Apigee proxy has proper CORS policies
2. **Connection Refused**: Verify the target server configuration
3. **Authentication Errors**: Check API key format and proxy policies
4. **Streaming Issues**: Ensure backend supports SSE format

### Debug Steps

1. Check browser developer tools for network errors
2. Verify proxy deployment status in Apigee console
3. Test target server connectivity
4. Review Apigee proxy logs for errors

## Development

### Local Development

For local development without Apigee:

```bash
# Start a local server
npm start

# Access at http://localhost:5200
```

### Customization

- **UI**: Modify CSS in the `<style>` section
- **API**: Update the fetch URL and request format
- **Authentication**: Add custom auth headers as needed

## Security Considerations

- API keys are sent as URL parameters (consider using headers for production)
- CORS policies should be properly configured
- Rate limiting should be implemented on the proxy
- HTTPS should be used in production

## Support

For issues or questions:
1. Check the Apigee proxy logs
2. Verify network connectivity
3. Review browser console for errors
4. Ensure all configuration steps are completed

---

**Note**: This demo requires a properly configured backend AI service that supports Server-Sent Events streaming format.
