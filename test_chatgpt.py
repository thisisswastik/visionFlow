from app.executor.browser import BrowserExecutor
import time

def test_chatgpt_interaction():
    print("Initializing BrowserExecutor...")
    # using headless=False to visually debug if it fails
    executor = BrowserExecutor(headless=False)
    
    try:
        print("Opening chatgpt.com...")
        executor.open("https://chatgpt.com")
        
        # Test 1: Typing text
        print("Typing message...")
        executor.type_by_placeholder("Ask anything", "capital of france")
        
        print("Wait for text to be typed...")
        time.sleep(2)
        
        # Test 2: Clicking button
        # The button to submit might have an aria-label like "Send prompt"
        print("Clicking submit button...")
        executor.click_by_text("Send prompt")
        
        print("Waiting for response...")
        time.sleep(5)
        print("Test completed successfully.")
    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        print("Closing browser...")
        executor.close()

if __name__ == "__main__":
    test_chatgpt_interaction()
