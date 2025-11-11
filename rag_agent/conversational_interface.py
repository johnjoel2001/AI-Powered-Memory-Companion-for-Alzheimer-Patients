#!/usr/bin/env python3
"""
Conversational Interface for Memory Assistant
Interactive chat interface for Alzheimer's patients to query their memories
"""

import os
from datetime import datetime
from memory_rag_agent import MemoryRAGAgent


class MemoryAssistant:
    def __init__(self):
        """Initialize the memory assistant"""
        self.agent = MemoryRAGAgent()
        self.conversation_history = []
        
    def start_conversation(self):
        """Start an interactive conversation"""
        print("="*60)
        print("MEMORY ASSISTANT - Here to help you remember")
        print("="*60)
        print("\nHello! I'm your memory assistant. I can help you remember")
        print("recent conversations, visitors, and activities.")
        print("\nYou can ask me questions like:")
        print("  - What did I do yesterday?")
        print("  - Who visited me this week?")
        print("  - Did I take my medication today?")
        print("  - What did Harry and I talk about?")
        print("\nType 'exit' or 'quit' to end the conversation.\n")
        
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                    print("\nAssistant: Take care! I'm here whenever you need me. 💙")
                    break
                
                # Add to conversation history
                self.conversation_history.append({
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Get response from agent
                response = self.agent.query_memories(user_input, days_back=7)
                
                # Add to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Display response
                print(f"\nAssistant: {response}")
                
            except KeyboardInterrupt:
                print("\n\nAssistant: Take care! I'm here whenever you need me. 💙")
                break
            except Exception as e:
                print(f"\nAssistant: I'm having trouble right now. Please try again. (Error: {e})")
    
    def get_conversation_history(self):
        """Return the conversation history"""
        return self.conversation_history


def main():
    """Main entry point"""
    assistant = MemoryAssistant()
    assistant.start_conversation()


if __name__ == "__main__":
    main()
