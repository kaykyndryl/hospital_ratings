# Azure OpenAI Integration Setup

This application now uses Azure OpenAI (GPT-4o) for intelligent hospital performance analysis and recommendations.

## Prerequisites

1. **Azure OpenAI Service**: Provisioned with GPT-4o model deployment
2. **Python 3.9+**
3. **pip** or your preferred package manager

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install the `openai` package (v1.3.0+) and all other dependencies.

### 2. Configure Azure OpenAI Credentials

#### Option A: Using .env file (Recommended for local development)

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Azure OpenAI credentials:
   ```
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview
   AZURE_OPENAI_API_KEY=your_api_key_here
   ```

3. The `.env` file is automatically loaded by the `python-dotenv` library when the app starts.

#### Option B: Environment Variables

Set directly in your shell or deployment platform:

```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource-name.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview"
export AZURE_OPENAI_API_KEY="your_api_key_here"
```

#### Option C: Azure Container Apps or similar platforms

Set environment variables directly in your deployment configuration.

### 3. Run the Application

```bash
streamlit run app.py
```

Or use the provided run script:

```bash
./run.sh
```

## Features

The app now leverages Azure OpenAI for:

1. **Intelligent Performance Analysis**
   - Detailed assessment of hospital metrics
   - Root cause analysis using AI patterns
   - Comparative insights vs. state and national benchmarks
   - Quality indicator summaries

2. **AI-Powered Recommendations**
   - Context-aware improvement strategies
   - Specific implementation steps
   - Expected impact projections
   - Implementation timelines
   - Priority-based ranking

3. **Session Caching**
   - Analysis results are cached during the session to avoid redundant API calls
   - Cache cleared on app restart
   - Reduces API costs and improves performance

## API Configuration Details

### Endpoint Format
Your Azure OpenAI endpoint should follow this pattern:
```
https://<your-resource-name>.cognitiveservices.azure.com/openai/deployments/<model-name>/chat/completions?api-version=2025-01-01-preview
```

### Expected Response Time
- Initial analysis: 3-10 seconds (depends on network and API load)
- Recommendations: 2-8 seconds
- Cached results: < 1 second

### Cost Considerations
- GPT-4o is used for analysis (~0.01-0.05 per hospital depending on complexity)
- Session caching helps reduce costs
- Consider batch analysis during off-peak hours for multiple hospitals

## Troubleshooting

### "Missing Azure OpenAI credentials" Error

**Solution**: Ensure `.env` file exists and contains:
```
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_KEY=your_api_key
```

### Connection Errors

**Solution**:
- Verify your endpoint URL is correct
- Check API key hasn't expired
- Ensure Azure OpenAI service is running
- Test with: `curl -X GET https://your-endpoint-url`

### JSON Parsing Error

**Solution**: This indicates OpenAI returned unexpected format
- Check that GPT-4o model is deployed correctly
- Verify API version in endpoint URL matches (2025-01-01-preview)
- Try again - may be transient

### Rate Limiting

**Solution**:
- Implement delays between requests
- Upgrade your Azure OpenAI quota
- Use session caching to avoid repeat analysis

## Performance Tips

1. **Cache Usage**: Analysis results are cached per hospital per state. Searching the same hospital multiple times costs nothing after first analysis.

2. **Batch Operations**: If analyzing many hospitals, do so in sequence to stay within rate limits.

3. **Off-Peak Analysis**: Run bulk hospital analysis during off-peak hours.

## Security

- Never commit `.env` file to version control (it's in `.gitignore`)
- Rotate API keys regularly
- Use Azure RBAC for role-based access control
- Monitor Azure OpenAI usage in Azure Portal

## API Limits

Default limits you should be aware of:
- Token limit per request: 2000 tokens output
- Temperature: 0.7 (balanced creativity and consistency)
- Model: GPT-4o (latest and most capable)

## Future Enhancements

- [ ] Batch analysis export
- [ ] Historical trend analysis using multiple snapshots
- [ ] Comparative analysis across hospital groups
- [ ] PDF report generation with AI insights
- [ ] Real-time CMS API integration for live data
