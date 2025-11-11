# MemerAI Backend Deployment Guide

## Deploy to Railway

### Step 1: Push to GitHub
```bash
cd /Users/johnrohit/Documents/hackathon-alzeimer/2025-AI-Hackathon
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### Step 2: Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Select the `rag_agent` folder as root

### Step 3: Set Environment Variables
In Railway dashboard, add these variables:
```
OPENAI_API_KEY=sk-proj-...
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJ...
PORT=5004
```

### Step 4: Deploy!
- Railway will auto-deploy
- You'll get a URL like: `https://memerai-production.up.railway.app`

---

## API Endpoints for iOS App

### Base URL
```
https://your-app.up.railway.app
```

### 1. Start Conversation
```http
POST /api/start
Content-Type: application/json

Response:
{
  "success": true,
  "session_id": "abc123...",
  "greeting": "Good morning John! 🌅",
  "question": "Do you remember what special occasion we celebrated yesterday?",
  "memory_id": "uuid...",
  "person": "rae",
  "event": "Celebration of 72nd birthday",
  "has_hint": true,
  "type": "conversation"
}
```

### 2. Submit Answer
```http
POST /api/answer
Content-Type: application/json

Body:
{
  "session_id": "abc123...",
  "answer": "birthday",
  "question": "Do you remember what special occasion we celebrated yesterday?",
  "type": "conversation"
}

Response:
{
  "success": true,
  "response": "Yes! That's absolutely right! It was your 72nd birthday. 🎂",
  "next_question": "Do you remember who came to visit you in the morning?",
  "type": "follow_up",
  "is_end": false,
  "score": {
    "correct": 1,
    "total": 1
  }
}
```

### 3. Ask Question (Optional - for patient questions)
```http
POST /api/ask
Content-Type: application/json

Body:
{
  "session_id": "abc123...",
  "question": "Who visited me yesterday?"
}

Response:
{
  "success": true,
  "answer": "Your sister Rae and your brother Harry came to visit you yesterday for your birthday! 💕"
}
```

---

## iOS Integration Example

```swift
struct MemerAIService {
    let baseURL = "https://your-app.up.railway.app"
    
    func startConversation() async throws -> ConversationStart {
        let url = URL(string: "\(baseURL)/api/start")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(ConversationStart.self, from: data)
    }
    
    func submitAnswer(sessionId: String, answer: String, question: String) async throws -> AnswerResponse {
        let url = URL(string: "\(baseURL)/api/answer")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = [
            "session_id": sessionId,
            "answer": answer,
            "question": question,
            "type": "conversation"
        ]
        request.httpBody = try JSONEncoder().encode(body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(AnswerResponse.self, from: data)
    }
}
```

---

## Testing Locally First
```bash
cd rag_agent
python3 memerai_ui.py
# Test at http://localhost:5004
```

---

## Environment Variables Needed
- `OPENAI_API_KEY` - Your OpenAI API key
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon/service key
- `PORT` - Port number (Railway sets this automatically)
