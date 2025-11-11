# Memory RAG Agent - Alzheimer's Memory Assistant

An Agentic RAG (Retrieval Augmented Generation) system that helps Alzheimer's patients remember conversations, visitors, and daily activities by building a knowledge graph from audio transcriptions and images.

## Features

### 🧠 Knowledge Graph
- **Conversation Summaries**: Automatically summarizes conversations with sentiment analysis
- **Person Interactions**: Tracks who visited and what was discussed
- **Memory Events**: Extracts important events (meals, medications, visitors, activities)
- **Topics & Key Points**: Identifies discussion topics and important points

### 🤖 Agentic RAG with Vector Embeddings
- **Semantic Search**: Uses OpenAI embeddings for intelligent similarity matching
- **Natural Language Queries**: Ask questions like "What did I do yesterday?"
- **Context-Aware Responses**: Uses retrieved memories to provide accurate answers
- **Temporal Reasoning**: Understands time-based queries (yesterday, this week, etc.)
- **Person-Centric**: Can query by person name ("What did Harry and I talk about?")
- **Vector Similarity**: Finds relevant memories even with different wording

### 📊 Data Processing
- **Automatic Analysis**: Processes audio transcriptions using GPT-4
- **Sentiment Detection**: Identifies emotional tone of conversations
- **Event Extraction**: Automatically detects important events
- **Batch Processing**: Can process all existing audio chunks at once

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Supabase Database                     │
├─────────────────────────────────────────────────────────┤
│  audio_chunks (transcriptions)                          │
│  images (detected persons)                              │
│  ↓                                                       │
│  conversation_summaries (summaries, sentiment, topics)  │
│  person_interactions (who, what, when)                  │
│  memory_events (important events)                       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              Memory RAG Agent (GPT-4)                    │
├─────────────────────────────────────────────────────────┤
│  • Analyzes transcriptions                              │
│  • Extracts insights                                    │
│  • Builds knowledge graph                               │
│  • Answers natural language queries                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│           Conversational Interface                       │
├─────────────────────────────────────────────────────────┤
│  "What did I do yesterday?"                             │
│  "Who visited me this week?"                            │
│  "Did I take my medication?"                            │
└─────────────────────────────────────────────────────────┘
```

## Setup

### 1. Install Dependencies
```bash
cd rag_agent
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-key"
export OPENAI_API_KEY="your-openai-api-key"
```

Or create a `.env` file:
```
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
OPENAI_API_KEY=your-openai-api-key
```

### 3. Create Database Tables
Run the SQL schema in Supabase SQL Editor:
```bash
cat knowledge_graph_schema.sql
```

## Usage

### Process All Audio Chunks (Build Knowledge Graph)
```bash
python batch_processor.py
```

This will:
- Find all audio chunks with transcriptions
- Analyze each one using GPT-4
- Extract summaries, sentiment, topics, events
- Store in knowledge graph tables

### Start Conversational Interface
```bash
python conversational_interface.py
```

Example conversation:
```
You: What did I do yesterday?
Assistant: Yesterday, you had a conversation with Harry about healthcare...

You: Who visited me this week?
Assistant: This week, you had visits from Harry and John...

You: Did I take my medication today?
Assistant: Based on the records, I can see...
```

### Process Single Audio Chunk
```bash
python batch_processor.py <audio_chunk_id>
```

### Programmatic Usage
```python
from memory_rag_agent import MemoryRAGAgent

agent = MemoryRAGAgent()

# Process an audio chunk
result = agent.process_audio_chunk("audio-chunk-id")
print(result['summary'])
print(result['sentiment'])
print(result['topics'])

# Query memories
answer = agent.query_memories("What did I do yesterday?")
print(answer)
```

## Knowledge Graph Schema

### conversation_summaries
- `summary`: Brief summary of conversation
- `sentiment`: positive/neutral/negative/mixed
- `topics`: Array of discussion topics
- `key_points`: Array of important points

### person_interactions
- `person_name`: Name of person
- `interaction_type`: conversation/visit/activity
- `context`: What was discussed or done

### memory_events
- `event_type`: meal/medication/visitor/activity/other
- `event_description`: What happened
- `participants`: Who was involved
- `importance_score`: 0.0 to 1.0

## Example Queries

**Time-based:**
- "What happened yesterday?"
- "What did I do this morning?"
- "Who visited me this week?"

**Person-based:**
- "What did Harry and I talk about?"
- "When did John visit me?"
- "Who have I seen recently?"

**Event-based:**
- "Did I take my medication?"
- "What did I eat for lunch?"
- "What activities did I do today?"

**Topic-based:**
- "What have we been discussing about healthcare?"
- "Did anyone mention Obama?"

## How It Works

1. **Data Collection**: Audio chunks and images are uploaded via the API
2. **Transcription**: Audio is transcribed using OpenAI Whisper
3. **Analysis**: GPT-4 analyzes transcriptions to extract:
   - Summaries and sentiment
   - Topics and key points
   - Important events
   - Person interactions
4. **Storage**: Insights stored in knowledge graph tables
5. **Retrieval**: When user asks a question:
   - Relevant memories are retrieved from database
   - Context is built from retrieved data
   - GPT-4 generates natural language answer
6. **Response**: User receives conversational, context-aware answer

## Benefits for Alzheimer's Patients

✅ **Memory Support**: Helps recall recent conversations and events
✅ **Social Connection**: Tracks who visited and what was discussed
✅ **Medication Tracking**: Can identify medication-related events
✅ **Activity Monitoring**: Keeps record of daily activities
✅ **Emotional Support**: Provides warm, conversational interface
✅ **Caregiver Insights**: Helps caregivers understand patient's day

## Future Enhancements

- [ ] Voice interface (speech-to-text input)
- [ ] Proactive reminders based on patterns
- [ ] Photo integration in responses
- [ ] Multi-language support
- [ ] Mobile app interface
- [ ] Family member access portal
- [ ] Trend analysis and reports
