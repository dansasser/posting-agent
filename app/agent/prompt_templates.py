# --- System Prompts ---

# The core persona for the AI social media copywriter.
# This guides the tone, style, and quality of all generated content.
COPYWRITER_SYSTEM_PROMPT = """
You are a precise and creative social media copywriter for Facebook.
Your mission is to generate clean, concise, and highly engaging content that is on-topic and drives user interaction.

Key principles:
1.  **Clarity is paramount:** Use simple, direct language. Avoid jargon and complexity.
2.  **Be concise:** Get to the point quickly. Every word must earn its place.
3.  **Stay on-topic:** Strictly adhere to the user's requested topic. Do not introduce unrelated ideas.
4.  **Engage deliberately:** End every post or comment with a question or a clear call-to-action.
5.  **Follow instructions:** Pay close attention to formatting requirements, such as length constraints and numbering.
"""

# --- Prompt Templates for Content Generation ---

def create_post_prompt(topic: str, style_guide: dict) -> str:
    """
    Creates a prompt for generating a main Facebook post.

    Args:
        topic: The central theme of the post.
        style_guide: A dictionary defining the desired style (e.g., tone, length).

    Returns:
        A formatted prompt string for the LLM.
    """
    return f"""
Generate a Facebook post about the following topic:
**Topic:** "{topic}"

**Style Guide:**
- **Tone:** {style_guide.get('tone', 'neutral')}
- **Length:** Between {style_guide.get('length_words', [20, 50])[0]} and {style_guide.get('length_words', [20, 50])[1]} words.
- **Call-to-Action:** The post MUST end with this exact phrase: "{style_guide.get('cta', 'What do you think?')}"

Generate ONLY the post content, without any extra commentary or quotation marks.
"""

def create_thread_comment_prompt(
    topic: str, main_post_content: str, comment_index: int, total_comments: int, style_guide: dict
) -> str:
    """
    Creates a prompt for generating a single comment in a thread.

    Args:
        topic: The central theme of the thread.
        main_post_content: The content of the initial post.
        comment_index: The 1-based index of the current comment.
        total_comments: The total number of comments in the thread.
        style_guide: A dictionary defining the desired style.

    Returns:
        A formatted prompt string for the LLM.
    """
    numbering = style_guide.get('numbering_scheme', '({i}/{n})').format(i=comment_index, n=total_comments)

    return f"""
You are writing a comment in a Facebook thread.
**Topic:** "{topic}"
**Main Post:** "{main_post_content}"

This is comment number {comment_index} out of {total_comments}.
It should continue the narrative or provide a new piece of information related to the main topic.

**Style Guide:**
- **Tone:** {style_guide.get('tone', 'informative')}
- **Length:** Between {style_guide.get('length_words', [30, 50])[0]} and {style_guide.get('length_words', [30, 50])[1]} words.
- **Prefix:** The comment MUST start with the prefix "{numbering} ".

Generate ONLY the comment content. Do not add extra commentary.
"""