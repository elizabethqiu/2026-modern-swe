from coding_agent import execute_llm_call

result = execute_llm_call([
    {"role": "assistant", "content": "You are a helpful assistant."},
    {"role": "user", "content": "say hello in french."}
])

print(result)