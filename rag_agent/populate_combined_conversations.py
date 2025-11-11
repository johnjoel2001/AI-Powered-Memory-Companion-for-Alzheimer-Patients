#!/usr/bin/env python3
"""
Populate combined_conversations table
Run this AFTER creating the table in Supabase
"""

from conversation_combiner import ConversationCombiner

print("="*60)
print("POPULATING COMBINED CONVERSATIONS")
print("="*60)

combiner = ConversationCombiner()

# Combine all conversations
print("\n1. Combining audio chunks...")
results = combiner.combine_all_conversations()

# Show summary
combiner.print_summary(results)

# Save to database
print("\n2. Saving to database...")
combiner.save_combined_conversations(results)

print("\n" + "="*60)
print("✅ DONE! Check Supabase 'combined_conversations' table")
print("="*60)
