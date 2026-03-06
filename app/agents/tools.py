from google.adk.tools import FunctionTool

@FunctionTool
def click_button(target: str) -> str:
    """Click a button by its visible text."""
    return f"Clicked {target}"

@FunctionTool
def type_text(target: str, text: str, enter: bool = False) -> str:
    """Type text into an input field by its placeholder. Set enter to True to submit after typing."""
    return f"Typed into {target}"

@FunctionTool
def scroll_page() -> str:
    """Scroll the page."""
    return "Scrolled page"

@FunctionTool
def finish() -> str:
    """Call this when the task is successfully completed."""
    return "Task completed"

@FunctionTool
def extract_page_content() -> str:
    """Extract all the visible text content from the current page."""
    return "Page content extracted"

@FunctionTool
def ask_customer_for_input(question: str) -> str:
    """Use this tool when you encounter a login screen, 2FA prompt, or need explicit information from the user (like a password). The execution will pause until the user responds."""
    return "User response pending"

