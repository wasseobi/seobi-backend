"""Summary prompts for background processing."""

SUMMARY_PROMPT = """You are an expert conversation summarizer. Create a concise summary of the following conversation analysis:

Analysis Results:
{analysis_results}

Additional Context:
- Total Messages: {message_count}
- Time Span: {time_span}
- Participants: {participants}

Please provide a summary that includes:
1. A brief overview of the conversation
2. Key decisions or conclusions reached
3. Important action items or next steps
4. Any notable concerns or highlights

Format your response as a JSON object with these keys:
- overview: A concise summary of the entire conversation
- key_decisions: List of important decisions or conclusions
- action_items: List of specific action items or next steps
- highlights: List of notable points or concerns
- confidence: Float between 0 and 1 indicating summary confidence
""" 