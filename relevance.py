import requests

def ask_mistral(question, context):
    prompt = f"""Is the following text inappropriate as a response to the question {context}? "{text}" 
Answer ONLY 'yes' or 'no' with no additional text or explanation."""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral:7b-instruct-v0.2-q4_0",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,  # Minimizes randomness
                "num_predict": 1,    # Forces short output
                "stop": ["\n"]       # Stops after first word
            }
        }
    )
    answer = response.json()["response"].strip().lower()
    print(f"Raw answer: {answer}")
    return answer == "yes"

# Example usage
text = "My family was really fucked up, but here's a lighthearted one: eating banana with the skin. "
context = "What’s something your family did that you assumed everyone’s family did—until someone looked horrified?"
print(ask_mistral(text, context))  # Output: False