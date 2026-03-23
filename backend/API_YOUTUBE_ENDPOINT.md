# YouTube Audio Extraction API

## Endpoint

`POST /api/upload/youtube`

## Description

Extracts audio from a YouTube video and stores it for transcription processing. The audio is automatically converted to MP3 format and limited to the first 15 minutes of the video.

## Authentication

Optional. If authenticated, files are organized by user ID. Anonymous users can also use this endpoint.

## Request

### Headers
- `Content-Type: application/json`
- `Authorization: Bearer <token>` (optional)

### Body
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Fields:**
- `url` (string, required): YouTube video URL. Supports both full URLs (`youtube.com/watch?v=...`) and short URLs (`youtu.be/...`)

## Response

### Success (200 OK)
```json
{
  "file_key": "uploads/user_123/abc-def-ghi.mp3",
  "file_size": 5242880,
  "file_format": "mp3",
  "duration": 180.5,
  "message": "YouTube audio extracted successfully"
}
```

**Fields:**
- `file_key` (string): Unique identifier for the stored audio file
- `file_size` (integer): Size of the audio file in bytes
- `file_format` (string): Audio format (always "mp3")
- `duration` (float): Duration of the audio in seconds
- `message` (string): Success message

### Error Responses

#### 400 Bad Request
Invalid URL or video restrictions.

**Examples:**
```json
{
  "detail": "YouTube URL is required"
}
```

```json
{
  "detail": "Invalid YouTube URL. Please provide a valid YouTube video URL."
}
```

```json
{
  "detail": "Video is private, unavailable, or restricted"
}
```

```json
{
  "detail": "Video is restricted due to copyright"
}
```

#### 413 Payload Too Large
Extracted audio exceeds size limit.

```json
{
  "detail": "Extracted audio exceeds maximum size limit of 100MB"
}
```

#### 500 Internal Server Error
Extraction or storage failure.

```json
{
  "detail": "Failed to extract audio from YouTube. Please try again or use direct file upload."
}
```

```json
{
  "detail": "Failed to store extracted audio"
}
```

## Limitations

- **Duration**: Maximum 15 minutes (900 seconds). Longer videos are automatically truncated.
- **File Size**: Maximum 100MB after extraction.
- **Supported URLs**: Only YouTube URLs (youtube.com, youtu.be).
- **Video Restrictions**: Private, age-restricted, or copyright-blocked videos cannot be processed.

## Examples

### cURL

```bash
# Anonymous user
curl -X POST "http://localhost:8000/api/upload/youtube" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Authenticated user
curl -X POST "http://localhost:8000/api/upload/youtube" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"url": "https://youtu.be/dQw4w9WgXcQ"}'
```

### JavaScript (Fetch API)

```javascript
// Anonymous user
const response = await fetch('http://localhost:8000/api/upload/youtube', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
  })
});

const data = await response.json();
console.log(data);

// Authenticated user
const response = await fetch('http://localhost:8000/api/upload/youtube', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
  })
});
```

### Python (requests)

```python
import requests

# Anonymous user
response = requests.post(
    'http://localhost:8000/api/upload/youtube',
    json={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'}
)
print(response.json())

# Authenticated user
headers = {'Authorization': f'Bearer {token}'}
response = requests.post(
    'http://localhost:8000/api/upload/youtube',
    json={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'},
    headers=headers
)
print(response.json())
```

## Notes

- The endpoint processes videos asynchronously but returns immediately after extraction
- Temporary files are automatically cleaned up after processing
- All operations are logged for monitoring and debugging
- The extracted audio is stored in S3-compatible storage (MinIO)
- For authenticated users, files are organized under `uploads/user_{user_id}/`
- For anonymous users, files are organized under `uploads/anonymous/`

## Related Endpoints

- `POST /api/upload` - Upload audio/video files directly
- `POST /api/upload/recording` - Upload browser-recorded audio
- `POST /api/transcriptions` - Create transcription from uploaded audio

## Troubleshooting

### "Invalid YouTube URL"
- Ensure the URL is from youtube.com or youtu.be
- Check for typos in the URL
- Remove any extra parameters or fragments

### "Video is private, unavailable, or restricted"
- The video may be set to private by the owner
- The video may have been deleted
- The video may be region-restricted
- Try using direct file upload instead

### "Video is restricted due to copyright"
- The video has copyright restrictions that prevent downloading
- Try using direct file upload instead

### "Extracted audio exceeds maximum size limit"
- The video's audio track is too large (>100MB)
- Try a shorter video or use a different source

## Security

- URL validation prevents non-YouTube URLs
- File size limits prevent abuse
- Temporary files are always cleaned up
- All errors are logged for monitoring
- User authentication is optional but recommended for better organization
