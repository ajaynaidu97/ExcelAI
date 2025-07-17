import re

def extract_code(text):
    """Extracts the first Python code block from markdown or plain text."""
    code_blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    if code_blocks:
        return code_blocks[0]
    # Fallback: try to find code-like lines
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines) 