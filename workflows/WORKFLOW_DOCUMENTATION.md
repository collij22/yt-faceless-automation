# YouTube Automation n8n Workflows Documentation

## Overview
This folder contains 5 production-ready n8n workflows for a complete YouTube automation system. All workflows follow n8n best practices, using standard nodes wherever possible and Code nodes only for complex logic.

## Workflows

### 1. TTS Generation Workflow (`tts_webhook_PRODUCTION.json`)

**Purpose:** Converts text to speech with automatic chunking for long content and multi-provider support.

**What it does:**
- Validates incoming text and slug parameters
- Automatically chunks text over 5000 characters at sentence boundaries
- Routes to different TTS providers (ElevenLabs, Google TTS, or mock)
- Aggregates multiple audio chunks into a single response
- Handles errors gracefully with validation feedback

**How to use:**
```bash
POST http://localhost:5678/webhook/tts-generation
Content-Type: application/json

{
  "text": "Your text content here",
  "slug": "video_identifier",
  "provider": "elevenlabs",  // optional, defaults to elevenlabs
  "voice_id": "voice_id",    // optional, has default
  "chunk_size": 5000,        // optional, max chars per chunk
  "language": "en"           // optional, defaults to en
}
```

**Response:**
```json
{
  "status": "success",
  "message": "TTS generation completed",
  "request": {
    "slug": "video_identifier",
    "text_length": 1234,
    "provider": "elevenlabs"
  },
  "output": {
    "total_chunks": 1,
    "files": ["video_identifier.mp3"],
    "format": "mp3_44100_128"
  }
}
```

**Key Features:**
- Smart text chunking preserves sentence boundaries
- Multi-provider support with fallback options
- Preserves all metadata through the pipeline
- Handles both single and multi-chunk scenarios

---

### 2. YouTube Upload Workflow (`youtube_upload_PRODUCTION.json`)

**Purpose:** Handles complete YouTube video upload process with metadata, thumbnails, and playlist management.

**What it does:**
- Validates title and description (required fields)
- Truncates title to 100 chars and description to 5000 chars
- Processes tags and ensures they meet YouTube limits
- Handles optional thumbnail upload
- Manages playlist additions
- Sets privacy, category, and monetization settings

**How to use:**
```bash
POST http://localhost:5678/webhook/youtube-upload
Content-Type: application/json

{
  "title": "Your Video Title",
  "description": "Video description here",
  "tags": ["tag1", "tag2", "tag3"],
  "category_id": "22",        // optional, defaults to People & Blogs
  "privacy": "private",        // optional: private/public/unlisted
  "thumbnail_url": "https://...", // optional
  "playlist_id": "PLxxxxx",   // optional
  "made_for_kids": false      // optional, defaults to false
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Video uploaded successfully",
  "video": {
    "id": "YT_abc123",
    "url": "https://youtube.com/watch?v=YT_abc123",
    "title": "Your Video Title",
    "privacy": "private"
  },
  "thumbnail": {
    "status": "uploaded",
    "url": "https://..."
  },
  "playlist": {
    "status": "added",
    "id": "PLxxxxx"
  }
}
```

**Key Features:**
- Automatic metadata validation and truncation
- Thumbnail handling with conditional processing
- Playlist management
- Unique video ID generation
- Tag processing with YouTube limits

---

### 3. YouTube Analytics Workflow (`youtube_analytics_PRODUCTION.json`)

**Purpose:** Retrieves channel analytics with insights, demographics, and traffic sources.

**What it does:**
- Fetches analytics for specified date range
- Generates mock metrics for testing (replace with YouTube API)
- Optional demographics data (age, gender, location)
- Optional traffic source analysis
- Generates AI-powered insights based on metrics
- Provides actionable recommendations

**How to use:**
```bash
POST http://localhost:5678/webhook/youtube-analytics
Content-Type: application/json

{
  "channel_id": "UC_your_channel",  // optional
  "date_range": "last_30_days",     // optional
  "start_date": "2024-01-01",       // optional, custom range
  "end_date": "2024-01-31",         // optional, custom range
  "include_demographics": true,      // optional, default true
  "include_traffic_sources": true    // optional, default true
}
```

**Response:**
```json
{
  "status": "success",
  "channel": {
    "id": "UC_your_channel",
    "period": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    }
  },
  "metrics": {
    "views": 50000,
    "watch_hours": 2000,
    "subscriber_change": 500,
    "revenue": 250.50,
    "ctr": 4.5
  },
  "demographics": {
    "age_group": "25-34",
    "gender_split": {
      "male": 60,
      "female": 40
    }
  },
  "insights": [
    "Low click-through rate detected",
    "Short average view duration"
  ],
  "recommendations": [
    "Improve thumbnails and titles",
    "Improve video hooks and pacing"
  ]
}
```

**Key Features:**
- Flexible date range options
- Smart insights generation based on metrics
- Optional demographic and traffic data
- Performance recommendations
- Comprehensive metric tracking

---

### 4. Cross-Platform Distribution Workflow (`cross_platform_PRODUCTION.json`)

**Purpose:** Distributes content across multiple social media platforms with platform-specific formatting.

**What it does:**
- Validates content title (required)
- Splits distribution across multiple platforms
- Applies platform-specific formatting rules
- Generates unique URLs for each platform
- Tracks distribution success
- Aggregates results across all platforms

**How to use:**
```bash
POST http://localhost:5678/webhook/cross-platform-distribute
Content-Type: application/json

{
  "title": "Your Content Title",
  "description": "Content description",
  "platforms": ["tiktok", "instagram", "twitter"],  // optional, has defaults
  "video_url": "https://...",  // optional
  "hashtags": ["viral", "trending"]  // optional
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Distributed to 3 platforms",
  "summary": {
    "total_platforms": 3,
    "successful": 3,
    "failed": 0
  },
  "platforms": [
    {
      "platform": "tiktok",
      "url": "https://tiktok.com/post/abc123",
      "posted": true
    },
    {
      "platform": "instagram",
      "url": "https://instagram.com/post/def456",
      "posted": true
    }
  ],
  "urls": {
    "tiktok": "https://tiktok.com/post/abc123",
    "instagram": "https://instagram.com/post/def456",
    "twitter": "https://twitter.com/post/ghi789"
  }
}
```

**Key Features:**
- Multi-platform batch processing
- Platform-specific content formatting
- Character limit handling per platform
- Success tracking and reporting
- URL generation for tracking

---

### 5. Affiliate Link Shortener Workflow (`affiliate_shortener_PRODUCTION.json`)

**Purpose:** Creates shortened affiliate links with UTM tracking, QR codes, and analytics.

**What it does:**
- Validates original URL
- Adds UTM parameters for tracking
- Detects affiliate program automatically
- Generates short link with custom or random code
- Optional QR code generation
- Prepares analytics tracking

**How to use:**
```bash
POST http://localhost:5678/webhook/affiliate-shorten
Content-Type: application/json

{
  "original_url": "https://amazon.com/dp/B08N5WRWNW",
  "title": "Product Name",           // optional
  "utm_source": "youtube",           // optional, defaults to youtube
  "utm_medium": "video",             // optional, defaults to video
  "utm_campaign": "review_2024",     // optional
  "custom_alias": "best-product",    // optional, generates random if not provided
  "generate_qr": true                // optional, defaults to true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Link shortened successfully",
  "link": {
    "original": "https://amazon.com/dp/B08N5WRWNW",
    "tracking": "https://amazon.com/dp/B08N5WRWNW?utm_source=youtube&utm_medium=video",
    "short": "https://short.link/abc123",
    "short_code": "abc123"
  },
  "tracking": {
    "utm_source": "youtube",
    "utm_medium": "video",
    "utm_campaign": "review_2024"
  },
  "affiliate": {
    "program": "Amazon Associates",
    "estimated_commission": "2-5%"
  },
  "qr_code": {
    "enabled": true,
    "url": "https://api.qrserver.com/v1/create-qr-code/?size=500x500&data=..."
  }
}
```

**Key Features:**
- Automatic affiliate program detection
- UTM parameter management
- QR code generation for offline tracking
- Custom or auto-generated short codes
- Analytics preparation

---

## Architecture & Best Practices

### Node Usage
- **Standard Nodes (80%)**: Set, If, Switch, Merge nodes for data manipulation
- **Code Nodes (20%)**: Only for complex logic like text chunking and aggregation
- **HTTP Request Nodes**: Ready for API integrations (currently mocked)

### Error Handling
- All workflows include input validation
- Error responses are properly formatted
- Graceful fallbacks for optional features

### Data Flow
1. **Webhook Entry**: All workflows start with POST webhook
2. **Validation**: Required fields are checked
3. **Processing**: Data transformation and enrichment
4. **Routing**: Conditional logic for features
5. **Response**: Aggregated, formatted response

---

## Testing

### Quick Test All Workflows
```bash
python auto_deploy_and_test.py
```

### Manual Testing with cURL

Test each workflow individually:

```bash
# TTS Test
curl -X POST http://localhost:5678/webhook/tts-generation \
  -H "Content-Type: application/json" \
  -d '{"text": "Test text", "slug": "test"}'

# Upload Test
curl -X POST http://localhost:5678/webhook/youtube-upload \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "description": "Test video"}'

# Analytics Test
curl -X POST http://localhost:5678/webhook/youtube-analytics \
  -H "Content-Type: application/json" \
  -d '{"channel_id": "UC_test"}'

# Distribution Test
curl -X POST http://localhost:5678/webhook/cross-platform-distribute \
  -H "Content-Type: application/json" \
  -d '{"title": "Test content"}'

# Shortener Test
curl -X POST http://localhost:5678/webhook/affiliate-shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://amazon.com/test"}'
```

---

## Integration with YouTube Automation System

These workflows integrate with your Python orchestrator (`src/yt_faceless/`) to provide:

1. **Content Pipeline**: Research → Script → TTS → Assembly → Upload
2. **Distribution**: Automatic cross-platform posting
3. **Analytics**: Performance tracking and optimization
4. **Monetization**: Affiliate link management
5. **Optimization**: Data-driven improvements

### Environment Variables

Configure in n8n for production:
```
ELEVENLABS_API_KEY=your_key
GOOGLE_API_KEY=your_key
YOUTUBE_API_KEY=your_key
```

### Next Steps

1. **Replace Mock Responses**: Update HTTP Request nodes with real API calls
2. **Add Authentication**: Configure OAuth2 for YouTube API
3. **Enhance Error Handling**: Add retry logic and detailed error messages
4. **Add Monitoring**: Connect to logging and monitoring systems
5. **Scale**: Deploy n8n with proper database and redis for production

---

## Troubleshooting

### Common Issues

**"Workflow has errors"**
- Check all nodes for red indicators in n8n
- Verify webhook path matches the endpoint
- Ensure workflow is activated

**"Missing required fields"**
- Check the request payload matches documentation
- Validate JSON formatting
- Include all required parameters

**"No response data"**
- Check webhook response mode is set to "Last Node"
- Verify all connections between nodes
- Check for errors in Function/Code nodes

### Support Files

- `auto_deploy_and_test.py` - Automated testing script
- `create_production_workflows.py` - Workflow generator
- `SOLUTION_GUIDE.md` - Troubleshooting guide

---

## Maintenance

### Updating Workflows
1. Export current workflow from n8n
2. Make changes in n8n interface
3. Test thoroughly
4. Export and save to this folder
5. Update this documentation

### Version Control
- Keep workflow JSON files in git
- Document changes in commit messages
- Tag releases for production deployments

---

*Last Updated: January 2025*
*n8n Version: 1.110.1*
*System: YouTube Automation Platform*