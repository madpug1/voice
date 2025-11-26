# Render Deployment Guide for RAG Phone System

## Prerequisites
- Render.com account (free)
- Your backend code ready
- Gemini API key
- Twilio account (we'll set up after deployment)

---

## Step 1: Prepare Your Files

Make sure your `backend` folder has these files:
- ✅ `main.py`
- ✅ `rag_engine.py`
- ✅ `twilio_handler.py`
- ✅ `requirements.txt`
- ✅ `Procfile` (just created)
- ✅ `runtime.txt` (just created)
- ✅ `data/pdfs/` folder with your PDF files

---

## Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Click **Get Started for Free**
3. Sign up with email or GitHub

---

## Step 3: Deploy Web Service

1. Click **New +** → **Web Service**
2. Choose **Deploy an existing image from a registry** → Skip this
3. Instead, choose **Public Git repository** or **Upload files**

### Option A: Upload Files (Easier)
1. Zip your entire `backend` folder
2. Upload the zip file
3. Render will extract and deploy

### Option B: Manual Configuration
1. Click **Configure manually**
2. Set these values:
   - **Name**: `rag-phone-bot`
   - **Region**: Choose closest to you
   - **Branch**: main (if using Git)
   - **Root Directory**: Leave blank or `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

---

## Step 4: Add Environment Variables

In Render dashboard, go to **Environment** tab and add:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | your_gemini_api_key_here |
| `PDF_DATA_DIR` | `./data/pdfs` |
| `CHROMA_DB_PATH` | `./chroma_db` |

**Note**: Don't add Twilio variables yet - we'll add them after getting Twilio credentials.

---

## Step 5: Deploy

1. Click **Create Web Service**
2. Wait 5-10 minutes for deployment
3. Once deployed, you'll see: **"Your service is live at https://rag-phone-bot-xxxx.onrender.com"**
4. **Copy this URL** - you'll need it!

---

## Step 6: Test Deployment

1. Visit `https://your-app-url.onrender.com`
2. You should see: `{"status":"running","message":"RAG API is operational"}`
3. If you see this, deployment is successful! ✅

---

## Step 7: Set Up Twilio

1. Go to [twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Sign up (free $15 credit)
3. Verify your phone number
4. Get a phone number:
   - Console → Phone Numbers → Buy a Number
   - Choose one with **Voice** capability
   - Click **Buy**
5. Copy these from dashboard:
   - **Account SID**
   - **Auth Token**
   - **Phone Number**

---

## Step 8: Add Twilio Credentials to Render

1. Back in Render dashboard → **Environment** tab
2. Add these variables:

| Key | Value |
|-----|-------|
| `TWILIO_ACCOUNT_SID` | your_account_sid |
| `TWILIO_AUTH_TOKEN` | your_auth_token |
| `TWILIO_PHONE_NUMBER` | your_twilio_number |

3. Click **Save Changes**
4. Render will auto-redeploy (takes 2-3 minutes)

---

## Step 9: Configure Twilio Webhook

1. Go to Twilio Console → **Phone Numbers** → **Manage** → **Active Numbers**
2. Click your phone number
3. Scroll to **Voice Configuration**
4. Under **A CALL COMES IN**:
   - Select **Webhook**
   - Enter: `https://your-render-url.onrender.com/voice/incoming`
   - Method: **HTTP POST**
5. Click **Save**

---

## Step 10: Test Your Phone System! 🎉

1. Call your Twilio phone number from your mobile
2. You should hear: *"Hello! I'm your AI knowledge assistant..."*
3. Speak your question
4. Listen to the AI response!

---

## Troubleshooting

### "Application Error" when calling
- Check Render logs: Dashboard → Logs
- Verify all environment variables are set
- Make sure webhook URL is correct

### Deployment failed
- Check `requirements.txt` has all dependencies
- Verify Python version in `runtime.txt`
- Check Render build logs for errors

### Slow first response
- Free tier has "cold starts" - first request takes 10-20 seconds
- Subsequent calls will be faster

---

## Cost Summary

- **Render Free Tier**: 750 hours/month (sufficient for testing)
- **Twilio Trial**: $15 credit (~100-150 calls)
- **After trial**: ~$0.10 per call + $1/month for phone number

---

**You're all set!** Your phone-based RAG system is now live and accessible worldwide! 🚀
