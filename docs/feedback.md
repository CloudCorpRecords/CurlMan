# Feedback System Documentation

The API Testing Studio includes a feedback collection system that allows users to submit their thoughts, suggestions, and bug reports directly through the application.

## How It Works

1. Users can access the feedback form through the "Feedback" button in the application sidebar
2. Feedback data is collected and stored in a structured format
3. Feedback entries are saved to a JSON file that can be committed to GitHub
4. Each feedback entry includes:
   - Timestamp
   - Category (Bug Report, Feature Request, General Feedback)
   - Description
   - User Environment Information
   - Contact Information (optional)

## Feedback Data Structure

```json
{
  "feedback_entries": [
    {
      "id": "unique_id",
      "timestamp": "ISO-8601 timestamp",
      "category": "bug_report|feature_request|general",
      "description": "User's feedback text",
      "environment": {
        "browser": "Browser information",
        "os": "Operating system",
        "app_version": "Application version"
      },
      "contact": {
        "email": "Optional email address"
      },
      "status": "new|in_progress|resolved"
    }
  ]
}
```

## Implementation Details

The feedback system is implemented using:
- Streamlit components for the user interface
- JSON file storage for persistence
- Automatic GitHub integration for feedback tracking

## Usage

To submit feedback:
1. Click the "Feedback" button in the sidebar
2. Select the feedback category
3. Enter your feedback
4. Provide optional contact information
5. Submit the form

## Processing Feedback

Feedback entries are:
1. Validated for required fields
2. Stored in `feedback/feedback_data.json`
3. Available for review by maintainers
4. Can be exported or analyzed as needed
