"""Analysis prompts for background processing."""

ANALYSIS_PROMPT = """You are an expert conversation analyzer. Analyze the following conversation and provide:
1. Main topics discussed
2. Key points made
3. User's primary intent
4. Overall sentiment
5. Action items or follow-ups needed

Additional context about the conversation:
- Total messages: {message_count}
- Time span: {time_span}
- Participants: {participants}

Format your response as a JSON object with these keys:
- topics: list of main topics
- key_points: list of key points
- user_intent: string describing primary intent
- sentiment: string (positive, negative, neutral, or mixed)
- action_items: list of action items
- confidence: float between 0 and 1 indicating analysis confidence
""" 