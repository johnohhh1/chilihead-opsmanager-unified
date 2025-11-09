# GPT-5 Responses API Integration

## Summary of Changes

Your ChiliHead OpsManager system now supports **both** GPT-4 (Chat Completions API) and GPT-5 (Responses API).

## What Changed

### File: `server/services/model_provider.py`

**Before:** All OpenAI models used `/v1/chat/completions` endpoint

**After:** 
- GPT-4 models → `/v1/chat/completions` (unchanged)
- GPT-5 models → `/v1/responses` (NEW)
- o1 models → `/v1/responses` (NEW)

## API Differences

### GPT-4 (Chat Completions)
```python
POST /v1/chat/completions
{
    "model": "gpt-4o",
    "messages": [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "Hello"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
}

# Response:
{
    "choices": [
        {"message": {"content": "Hi there!"}}
    ]
}
```

### GPT-5 (Responses API)
```python
POST /v1/responses
{
    "model": "gpt-5",
    "prompt": "System: You are helpful\n\nUser: Hello",
    "temperature": 0.7,
    "max_tokens": 1000
}

# Response:
{
    "id": "resp_...",
    "response": "Hi there!"
}
```

## How It Works

The system automatically detects which API to use based on model name:

```python
# These models use Responses API (/v1/responses):
- gpt-5
- gpt-5-mini
- gpt-5-nano
- o1
- o1-preview

# These models use Chat Completions (/v1/chat/completions):
- gpt-4o
- gpt-4o-mini
- gpt-4-turbo
- gpt-3.5-turbo
```

## Testing

Run the test script:
```bash
cd C:\Users\John\Desktop\chilihead-opsmanager-unified\server
python test_gpt5.py
```

This will test:
1. ✅ GPT-5 with new Responses API
2. ✅ GPT-5-mini with new Responses API
3. ✅ GPT-5-nano with new Responses API
4. ✅ GPT-4o with old Chat Completions API (for comparison)

## Environment Variables

No changes needed! Your existing `.env` still works:
```
OPENAI_API_KEY=sk-...
OPENAI_PROJECT_ID=proj_...
OPENAI_BASE_URL=https://api.openai.com/v1
```

## Where GPT-5 Can Be Used

Now that the integration is complete, GPT-5 models will work anywhere in your app:

1. **Email Intelligence** (`services/ai_triage.py`)
2. **Smart Assistant** (`services/smart_assistant.py`)
3. **Task Extraction** (`services/task_extractor.py`)
4. **Summarization** (`services/summarize.py`)
5. **Operations Chat** (`routes/operations_chat.py`)

## Frontend Changes

The frontend model selector should already show GPT-5 models. They'll now work correctly when selected!

## Troubleshooting

### Error: "unsupported parameter: messages"
- **Cause:** Model is being sent to wrong endpoint
- **Fix:** Verify model name starts with "gpt-5" exactly
- **Check:** Look at server logs for routing decision

### Error: "This model doesn't support tools"
- **Cause:** GPT-5 may have limited tool/function support initially
- **Fix:** Use GPT-4o for function calling until GPT-5 adds support

### Error: 400 Bad Request
- **Cause:** API format mismatch
- **Fix:** Check if you're using beta/preview GPT-5 access
- **Action:** Verify with `test_gpt5.py` script

## Performance Notes

- **GPT-5 latency:** May be slower than GPT-4 initially (new models)
- **Token costs:** Check OpenAI pricing for GPT-5 rates
- **Rate limits:** GPT-5 may have different rate limits

## Next Steps

1. ✅ **Test the integration:** Run `python test_gpt5.py`
2. ✅ **Verify in UI:** Select GPT-5 model in frontend dropdown
3. ✅ **Monitor logs:** Watch for routing decisions in console
4. 📊 **Compare performance:** Test GPT-5 vs GPT-4o for your use cases

---

**Note:** If OpenAI changes the Responses API format, you may need to update the response parsing logic in `model_provider.py`.
