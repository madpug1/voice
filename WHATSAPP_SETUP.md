# WhatsApp Voice Note Setup Guide

## Quick Setup (5 Minutes)

### 1. Set Up Twilio WhatsApp Sandbox

1. Go to Twilio Console: https://console.twilio.com/
2. Navigate to **Messaging** → **Try it out** → **Send a WhatsApp message**
3. You'll see:
   - A sandbox number (e.g., `+1 415 523 8886`)
   - A join code (e.g., `join happy-tiger`)

4. **Activate the sandbox**:
   - Open WhatsApp on your phone
   - Send a message to the sandbox number: `join happy-tiger` (use your actual code)
   - You'll get a confirmation message

### 2. Configure Webhook

In the Twilio WhatsApp Sandbox settings:

1. Find **"When a message comes in"**
2. Enter your Render URL: `https://your-app-url.onrender.com/whatsapp/incoming`
3. Method: **HTTP POST**
4. Click **Save**

### 3. Add Environment Variables (If Not Already Added)

In Render Dashboard → Environment:
- `TWILIO_ACCOUNT_SID`: Your Account SID
- `TWILIO_AUTH_TOKEN`: Your Auth Token
- `GEMINI_API_KEY`: Your Gemini API key

### 4. Deploy

```powershell
git add .
git commit -m "Add WhatsApp voice note integration"
git push
```

Render will auto-deploy!

---

## How to Use

### Send Voice Notes:

1. Open WhatsApp
2. Go to your chat with the Twilio sandbox number
3. **Record and send a voice note** with your question
4. Wait a few seconds
5. You'll get a text response with:
   - What you said (transcription)
   - The AI's answer

### Example:

**You**: 🎤 *Voice note: "What is this document about?"*

**Bot**: 
```
🎤 You said: What is this document about?

Based on the documents in my knowledge base, this document discusses...
```

---

## Features

✅ **Voice Notes**: Send voice messages  
✅ **Text Messages**: Also works with text  
✅ **Speech-to-Text**: Automatic transcription  
✅ **RAG Integration**: Queries your PDFs  
✅ **100% Free**: No calling charges  

---

## Troubleshooting

### "I didn't get a response"
- Check Render logs for errors
- Verify webhook URL is correct
- Make sure environment variables are set

### "Audio transcription failed"
- Speak clearly
- Avoid background noise
- Try sending a text message to test if RAG works

### "Sandbox expired"
- Twilio sandbox expires after 3 days of inactivity
- Just send `join <code>` again to reactivate

---

## Production (Optional)

For production with your own WhatsApp Business number:
1. Apply for WhatsApp Business API
2. Get approved by Meta (1-2 weeks)
3. Update webhook to production number
4. Cost: ~$0.005 per message

---

**You're all set!** Send a voice note and test it out! 🎉
