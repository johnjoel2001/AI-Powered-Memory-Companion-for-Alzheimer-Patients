# MemorAI API - iOS Integration Guide

## 🚀 API Base URL
```
https://2025-ai-hackathon-raspberry-api-api-production-5bd5.up.railway.app
```

**Note:** This is deployed on Railway and works 24/7! No need to keep your laptop running.

---

## 📱 Quick Start for iOS

### API Endpoints

#### 1. Start Conversation
```http
POST /api/start
Content-Type: application/json

Response:
{
  "success": true,
  "session_id": "abc123def456",
  "greeting": "Good morning John! 🌅",
  "question": "Do you remember what special occasion we celebrated yesterday?",
  "memory_id": "uuid-here",
  "person": "rae",
  "event": "Celebration of 72nd birthday",
  "has_hint": true,
  "type": "conversation"
}
```

#### 2. Submit Answer
```http
POST /api/answer
Content-Type: application/json

Body:
{
  "session_id": "abc123def456",
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

#### 3. Ask Question (Optional - for mid-conversation questions)
```http
POST /api/ask
Content-Type: application/json

Body:
{
  "session_id": "abc123def456",
  "question": "Who visited me yesterday?"
}

Response:
{
  "success": true,
  "answer": "Your sister Rae and your brother Harry came to visit you yesterday for your birthday! 💕"
}
```

---

## 💻 Swift Implementation

### Models
```swift
struct ConversationStart: Codable {
    let success: Bool
    let sessionId: String
    let greeting: String
    let question: String
    let memoryId: String
    let person: String
    let event: String
    let hasHint: Bool
    let type: String
    
    enum CodingKeys: String, CodingKey {
        case success
        case sessionId = "session_id"
        case greeting, question
        case memoryId = "memory_id"
        case person, event
        case hasHint = "has_hint"
        case type
    }
}

struct AnswerResponse: Codable {
    let success: Bool
    let response: String
    let nextQuestion: String?
    let type: String
    let isEnd: Bool
    let score: Score
    
    enum CodingKeys: String, CodingKey {
        case success, response
        case nextQuestion = "next_question"
        case type
        case isEnd = "is_end"
        case score
    }
}

struct Score: Codable {
    let correct: Int
    let total: Int
}

struct AskResponse: Codable {
    let success: Bool
    let answer: String
}
```

### Service Class
```swift
import Foundation

class MemerAIService {
    let baseURL = "https://2025-ai-hackathon-raspberry-api-api-production-5bd5.up.railway.app"
    
    // Start a new conversation
    func startConversation() async throws -> ConversationStart {
        let url = URL(string: "\(baseURL)/api/start")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
        
        return try JSONDecoder().decode(ConversationStart.self, from: data)
    }
    
    // Submit an answer
    func submitAnswer(sessionId: String, answer: String, question: String) async throws -> AnswerResponse {
        let url = URL(string: "\(baseURL)/api/answer")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "session_id": sessionId,
            "answer": answer,
            "question": question,
            "type": "conversation"
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
        
        return try JSONDecoder().decode(AnswerResponse.self, from: data)
    }
    
    // Ask a question mid-conversation
    func askQuestion(sessionId: String, question: String) async throws -> AskResponse {
        let url = URL(string: "\(baseURL)/api/ask")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "session_id": sessionId,
            "question": question
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
        
        return try JSONDecoder().decode(AskResponse.self, from: data)
    }
}

enum APIError: Error {
    case invalidResponse
    case networkError
}
```

### Example Usage in SwiftUI
```swift
import SwiftUI

struct ConversationView: View {
    @StateObject private var viewModel = ConversationViewModel()
    
    var body: some View {
        VStack(spacing: 20) {
            // Greeting
            if let greeting = viewModel.greeting {
                Text(greeting)
                    .font(.title2)
                    .padding()
            }
            
            // Current Question
            if let question = viewModel.currentQuestion {
                Text(question)
                    .font(.headline)
                    .padding()
                    .background(Color.blue.opacity(0.1))
                    .cornerRadius(10)
            }
            
            // Answer Input
            TextField("Your answer...", text: $viewModel.userAnswer)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .padding()
            
            Button("Submit") {
                Task {
                    await viewModel.submitAnswer()
                }
            }
            .buttonStyle(.borderedProminent)
            
            // Response
            if let response = viewModel.botResponse {
                Text(response)
                    .padding()
                    .background(Color.green.opacity(0.1))
                    .cornerRadius(10)
            }
            
            // Score
            if viewModel.score.total > 0 {
                Text("Score: \(viewModel.score.correct)/\(viewModel.score.total)")
                    .font(.caption)
                    .foregroundColor(.gray)
            }
        }
        .padding()
        .onAppear {
            Task {
                await viewModel.startConversation()
            }
        }
    }
}

@MainActor
class ConversationViewModel: ObservableObject {
    @Published var greeting: String?
    @Published var currentQuestion: String?
    @Published var userAnswer: String = ""
    @Published var botResponse: String?
    @Published var score: (correct: Int, total: Int) = (0, 0)
    
    private var sessionId: String?
    private let service = MemerAIService()
    
    func startConversation() async {
        do {
            let response = try await service.startConversation()
            self.greeting = response.greeting
            self.currentQuestion = response.question
            self.sessionId = response.sessionId
        } catch {
            print("Error starting conversation: \(error)")
        }
    }
    
    func submitAnswer() async {
        guard let sessionId = sessionId,
              let question = currentQuestion else { return }
        
        do {
            let response = try await service.submitAnswer(
                sessionId: sessionId,
                answer: userAnswer,
                question: question
            )
            
            self.botResponse = response.response
            self.currentQuestion = response.nextQuestion
            self.score = (response.score.correct, response.score.total)
            self.userAnswer = ""
            
            if response.isEnd {
                // Conversation ended
                print("Conversation completed!")
            }
        } catch {
            print("Error submitting answer: \(error)")
        }
    }
}
```

---

## 🎯 Key Features

### Smart Answer Matching
The backend uses **3-tier matching**:
1. **Exact match** - "cake" = "cake"
2. **Fuzzy match** - "choclate" ≈ "chocolate" (typo tolerance)
3. **Semantic match** - "pastry" ≈ "cake" (GPT-powered)

### Progressive Hints
- Wrong answers trigger increasingly specific hints
- Uses rich family context (ages, personalities, fun facts)
- 4 levels of hints before revealing the answer

### Mid-Conversation Questions
- Patient can ask questions anytime
- "Who visited me?" gets answered
- Conversation continues after

---

## 📝 Example Flow

```
1. Start Conversation
   → GET greeting + first question

2. User: "birthday"
   → BOT: "Yes! That's right! Who came to visit?"

3. User: "tim" (wrong)
   → BOT: "Think about your younger sister - 62 years old..."

4. User: "rae" (correct)
   → BOT: "Yes! Your sister Rae came to visit."

5. Continue until conversation ends (is_end: true)
```

---

## 🔧 Testing

### Test with cURL
```bash
# Start conversation
curl -X POST https://2025-ai-hackathon-raspberry-api-api-production-5bd5.up.railway.app/api/start \
  -H "Content-Type: application/json"

# Submit answer
curl -X POST https://2025-ai-hackathon-raspberry-api-api-production-5bd5.up.railway.app/api/answer \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "answer": "birthday",
    "question": "Do you remember what special occasion we celebrated yesterday?",
    "type": "conversation"
  }'
```

---

## ⚠️ Important Notes

1. **Session Management**: Save the `session_id` from `/api/start` and use it for all subsequent calls
2. **Question Tracking**: Always send the current question when submitting an answer
3. **End Detection**: Check `is_end` field to know when conversation is complete
4. **Error Handling**: Always check `success` field in responses

---

## 🎨 UI/UX Tips

- Show the greeting prominently
- Display questions in a chat-like interface
- Show hints progressively (don't reveal all at once)
- Hide scores from patient (only show to caregiver)
- Use warm, encouraging language
- Add emojis for visual appeal 🎂💕🎁

---

## 📞 Support

If you have questions or issues:
- Check the response `success` field
- Look at error messages in the response
- Test endpoints with cURL first
- Contact: John

---

**Happy coding! 🚀📱**
