from groq import Groq
import os

# Fixed: Explicit check for the API key to prevent silent startup crashes
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    # Optional: Fallback string if your terminal profile environment didn't export it
    # api_key = "gsk_your_actual_fallback_key_here"
    print("WARNING: GROQ_API_KEY environment variable is not set!")

client = Groq(api_key=api_key)

def generate_summary(prompt: str) -> str:
    try:
        print("Calling Groq...")

        # Fixed: Adjusted max_tokens up so summaries do not cut off mid-sentence
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Production recommended 70B variant
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=250,  # Increased from 50 to allow full paragraph summaries
            temperature=0.3   # Added low temperature for consistent classification/summaries
        )

        print("Groq Response Received")
        
        # Guard clause against empty API choice arrays
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            return "ERROR: Groq returned an empty response array."

    except Exception as e:
        print("ERROR:", str(e))
        return f"ERROR: {str(e)}"

