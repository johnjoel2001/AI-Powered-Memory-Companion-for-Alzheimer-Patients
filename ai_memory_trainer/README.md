# AI Memory Trainer

Interactive memory training sessions using OpenAI's language models.

## Features

- **Warm-up phase**: Friendly conversation to ease into the session
- **Question-based training**: Uses stored Q&A database with retry logic
- **Intelligent evaluation**: LLM evaluates answers with hints for incorrect responses
- **Session tracking**: Tracks attempts, success rates, and timestamps
- **Conversation logging**: Saves complete session history

## Setup

```bash
pip install -r requirements.txt
```

Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-key-here"
```

## Usage

Run a training session:
```bash
python memory_trainer.py
```

With options:
```bash
python memory_trainer.py --num-questions 5 --model gpt-5-mini-2025-08-07
```

Configure timeouts:
```bash
python memory_trainer.py --warmup-timeout 180 --question-timeout 30 --max-session 900
```

**Note**: GPT-5 models only support default temperature (1.0) - custom temperature values are not supported.

## Timeout Configuration

The system implements timeouts at multiple levels:
- **Warm-up timeout** (default: 300s / 5 min): Maximum duration for the warm-up phase
- **Question timeout** (default: 60s): Time limit per question attempt
- **Max session duration** (default: 1800s / 30 min): Overall session time limit
- **User input timeout**: Automatically uses remaining time or 60s per input prompt

## Architecture

- **MemoryTrainer**: Main class managing session flow and conversation state
- **QADatabase**: Stores questions with metadata (practice times, success rate, timestamps)
- **Conversation State**: Full history maintained for context-aware interactions

## Workflow

1. **Initialize**: Load Q&A database and select questions by least recent use
2. **Warm-up** (up to 5 min): Casual conversation with the user - with timeout enforcement
3. **Training**: Ask questions with retry logic (max 3 attempts per question) - each attempt times out after 60s
4. **Evaluation**: LLM evaluates answers and provides progressive hints (never reveals answer directly)
5. **Summary**: Positive reinforcement and session statistics
6. **Cleanup**: Update database and save session log

All phases respect timeout limits. Session automatically ends if maximum duration is reached.

## Database Schema

Each QA entry tracks:
- Question and expected answer
- Creation time
- Practice times (how many times asked)
- Success rate (0.0 - 1.0)
- Last use time (for scheduling)
