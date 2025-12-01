# AssemblyAI Setup for Voice Transcription

## Get Your Free AssemblyAI API Key

AssemblyAI offers a generous free tier (100 hours/month) for voice transcription.

### Step 1: Sign Up

1. Go to: https://www.assemblyai.com/
2. Click **"Get API Key"** or **"Sign Up"**
3. Create a free account (email + password)

### Step 2: Get API Key

1. After signing up, you'll be redirected to the dashboard
2. Your API key will be displayed immediately
3. It looks like: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
4. **Copy it**

### Step 3: Add to Render

1. Go to your Render dashboard
2. Click on your service
3. Go to **Environment** tab
4. Add new environment variable:
   - **Key**: `ASSEMBLYAI_API_KEY`
   - **Value**: `your_api_key_here`
5. Click **Save Changes**

Render will automatically redeploy with the new environment variable.

---

## How It Works

- **Voice notes**: Automatically transcribed by AssemblyAI
- **Text messages**: Work as before
- **Free tier**: 100 hours/month (more than enough for testing)
- **Quality**: Better than Google Speech Recognition
- **Python 3.13**: Fully compatible!

---

## Test It

Once deployed:
1. Send a voice note to your WhatsApp sandbox
2. AssemblyAI transcribes it
3. RAG processes the question
4. You get the answer!

---

**That's it!** Much simpler than the previous setup and works perfectly with Python 3.13.
