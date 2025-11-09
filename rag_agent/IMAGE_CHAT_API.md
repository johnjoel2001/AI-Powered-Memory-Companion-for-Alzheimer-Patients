# MemorEye Image Chat API - iOS Integration Guide

## 🚀 API Base URL
```
https://sparklingly-kempt-terese.ngrok-free.dev
```

**Note:** This is the SAME ngrok URL, but now pointing to port 5005 (Image Chat)

---

## 📱 Quick Start for iOS

### API Endpoints

#### 1. Start Image Conversation
```http
POST /api/start
Content-Type: application/json

Response:
{
  "success": true,
  "session_id": "abc123def456",
  "greeting": "Good morning John! 🌅",
  "image_url": "https://aidxatmnfpmhxxpkmnny.supabase.co/storage/v1/object/public/images/...",
  "question": "Hello John! 🌅 Do you remember who this person is?",
  "total_questions": 2
}
```

#### 2. Submit Answer
```http
POST /api/answer
Content-Type: application/json

Body:
{
  "session_id": "abc123def456",
  "answer": "harry"
}

Response (Correct):
{
  "success": true,
  "correct": true,
  "response": "Yes! That's wonderful! This is Harry, your younger brother! 💕",
  "image_url": "https://...next-photo...",
  "next_question": "Hello John! 🌅 Do you remember who this person is?",
  "is_end": false,
  "score": {
    "correct": 1,
    "total": 2
  }
}

Response (Wrong - gives hint):
{
  "success": true,
  "correct": false,
  "response": "That's okay, John. Think about your younger brother - the 66-year-old inventor.",
  "is_end": false
}

Response (End):
{
  "success": true,
  "correct": true,
  "response": "Yes! That's wonderful! This is Rae, your younger sister! 💕",
  "is_end": true,
  "final_message": "🎉 You did wonderfully today, John! You remembered everyone! I'm so proud of you! 💕",
  "score": {
    "correct": 2,
    "total": 2
  }
}
```

---

## 💻 Swift Implementation

### Models
```swift
struct ImageConversationStart: Codable {
    let success: Bool
    let sessionId: String
    let greeting: String
    let imageUrl: String
    let question: String
    let totalQuestions: Int
    
    enum CodingKeys: String, CodingKey {
        case success
        case sessionId = "session_id"
        case greeting
        case imageUrl = "image_url"
        case question
        case totalQuestions = "total_questions"
    }
}

struct ImageAnswerResponse: Codable {
    let success: Bool
    let correct: Bool
    let response: String
    let imageUrl: String?
    let nextQuestion: String?
    let isEnd: Bool
    let finalMessage: String?
    let score: Score?
    
    enum CodingKeys: String, CodingKey {
        case success, correct, response
        case imageUrl = "image_url"
        case nextQuestion = "next_question"
        case isEnd = "is_end"
        case finalMessage = "final_message"
        case score
    }
}

struct Score: Codable {
    let correct: Int
    let total: Int
}
```

### Service Class
```swift
import Foundation
import UIKit

class ImageMemoryService {
    let baseURL = "https://sparklingly-kempt-terese.ngrok-free.dev"
    
    // Start image conversation
    func startImageConversation() async throws -> ImageConversationStart {
        let url = URL(string: "\(baseURL)/api/start")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
        
        return try JSONDecoder().decode(ImageConversationStart.self, from: data)
    }
    
    // Submit answer
    func submitAnswer(sessionId: String, answer: String) async throws -> ImageAnswerResponse {
        let url = URL(string: "\(baseURL)/api/answer")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "session_id": sessionId,
            "answer": answer
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
        
        return try JSONDecoder().decode(ImageAnswerResponse.self, from: data)
    }
    
    // Load image from URL
    func loadImage(from urlString: String) async throws -> UIImage {
        guard let url = URL(string: urlString) else {
            throw APIError.invalidURL
        }
        
        let (data, _) = try await URLSession.shared.data(from: url)
        
        guard let image = UIImage(data: data) else {
            throw APIError.invalidImage
        }
        
        return image
    }
}

enum APIError: Error {
    case invalidResponse
    case invalidURL
    case invalidImage
    case networkError
}
```

### SwiftUI Example
```swift
import SwiftUI

struct ImageMemoryView: View {
    @StateObject private var viewModel = ImageMemoryViewModel()
    
    var body: some View {
        VStack(spacing: 20) {
            // Greeting
            if let greeting = viewModel.greeting {
                Text(greeting)
                    .font(.title2)
                    .padding()
            }
            
            // Photo
            if let image = viewModel.currentImage {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFit()
                    .frame(maxHeight: 400)
                    .cornerRadius(15)
                    .shadow(radius: 10)
                    .padding()
            } else {
                ProgressView()
                    .frame(height: 400)
            }
            
            // Question
            if let question = viewModel.currentQuestion {
                Text(question)
                    .font(.headline)
                    .padding()
                    .background(Color.blue.opacity(0.1))
                    .cornerRadius(10)
            }
            
            // Answer Input
            TextField("Who is this?", text: $viewModel.userAnswer)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .padding()
            
            Button("Submit") {
                Task {
                    await viewModel.submitAnswer()
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isLoading)
            
            // Response
            if let response = viewModel.botResponse {
                Text(response)
                    .padding()
                    .background(viewModel.lastAnswerCorrect ? Color.green.opacity(0.1) : Color.orange.opacity(0.1))
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
class ImageMemoryViewModel: ObservableObject {
    @Published var greeting: String?
    @Published var currentImage: UIImage?
    @Published var currentQuestion: String?
    @Published var userAnswer: String = ""
    @Published var botResponse: String?
    @Published var score: (correct: Int, total: Int) = (0, 0)
    @Published var isLoading: Bool = false
    @Published var lastAnswerCorrect: Bool = false
    
    private var sessionId: String?
    private let service = ImageMemoryService()
    
    func startConversation() async {
        isLoading = true
        
        do {
            let response = try await service.startImageConversation()
            self.greeting = response.greeting
            self.currentQuestion = response.question
            self.sessionId = response.sessionId
            self.score = (0, response.totalQuestions)
            
            // Load image
            self.currentImage = try await service.loadImage(from: response.imageUrl)
        } catch {
            print("Error starting conversation: \(error)")
            self.botResponse = "Failed to start conversation"
        }
        
        isLoading = false
    }
    
    func submitAnswer() async {
        guard let sessionId = sessionId else { return }
        
        isLoading = true
        
        do {
            let response = try await service.submitAnswer(
                sessionId: sessionId,
                answer: userAnswer
            )
            
            self.botResponse = response.response
            self.lastAnswerCorrect = response.correct
            
            if let score = response.score {
                self.score = (score.correct, score.total)
            }
            
            if response.correct {
                self.userAnswer = ""
                
                if response.isEnd {
                    // Show final message
                    if let finalMessage = response.finalMessage {
                        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
                            self.botResponse = finalMessage
                        }
                    }
                } else if let nextImageUrl = response.imageUrl,
                          let nextQuestion = response.nextQuestion {
                    // Load next image and question
                    self.currentImage = try await service.loadImage(from: nextImageUrl)
                    self.currentQuestion = nextQuestion
                    self.botResponse = nil
                }
            } else {
                // Wrong answer - hint given, try again
                self.userAnswer = ""
            }
        } catch {
            print("Error submitting answer: \(error)")
            self.botResponse = "Failed to submit answer"
        }
        
        isLoading = false
    }
}
```

---

## 🎯 Key Features

### Progressive Hints
Wrong answers trigger increasingly specific hints:
1. **Hint 1:** "Think about your younger brother - the 66-year-old inventor."
2. **Hint 2:** "He loves building gadgets in his garage!"
3. **Hint 3:** "His name starts with 'H' - he names his tools!"
4. **Hint 4:** "It's Harry, John! Your brother Harry!"

### Smart Photo Selection
- Queries database by `detected_persons` column
- Each person gets unique photo (no duplicates)
- Shows photos in order: Harry → Rae

### Answer Matching
Accepts multiple variations:
- "harry" ✅
- "brother" ✅
- "Harry" ✅
- "my brother" ✅

---

## 📝 Example Flow

```
1. Start Conversation
   → Shows Harry's photo
   → "Do you remember who this person is?"

2. User: "tim" (wrong)
   → "Think about your younger brother..."

3. User: "harry" (correct)
   → "Yes! That's Harry!"
   → Shows Rae's photo
   → "Do you remember who this person is?"

4. User: "rae" (correct)
   → "Yes! That's Rae!"
   → "🎉 You did wonderfully!"
```

---

## 🔧 Testing

### Test with cURL
```bash
# Start conversation
curl -X POST https://sparklingly-kempt-terese.ngrok-free.dev/api/start \
  -H "Content-Type: application/json"

# Submit answer
curl -X POST https://sparklingly-kempt-terese.ngrok-free.dev/api/answer \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "answer": "harry"
  }'
```

---

## ⚠️ Important Notes

1. **Image Loading**: Always load images asynchronously
2. **Session Management**: Save `session_id` from `/api/start`
3. **Progressive Hints**: Don't move to next question until correct answer
4. **End Detection**: Check `is_end` field to know when done
5. **Score Display**: Hide from patient, show only to caregiver

---

## 🎨 UI/UX Tips

- Show large, clear photos (400px height)
- Use warm, encouraging language
- Display hints progressively
- Celebrate correct answers with animations
- Hide scores from patient view
- Use emojis for visual appeal 🖼️💕

---

## 📞 Support

**API Running On:**
- Port 5005 (local)
- ngrok URL (public)

**Keep Running:**
- Flask app on port 5005
- ngrok tunnel

---

**Happy coding! 🚀📱🖼️**
