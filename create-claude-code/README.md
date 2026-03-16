# create an LLM (like Claude Code) in ~200 lines

setup (module level):

- `TOOL_REGISTRY` = { "read_file": fn, "list_files": fn, ... }
- `get_tool_str_representation(name)` reads fn.__doc__ + inspect.signature()
- `get_full_system_prompt` loops registry, builds formatted tool list, injects into SYSTEM_PROMPT

called at runtime:  `run_coding_agent_loop()` is the entry point.
1. outer `while True` loop: wait for user input, conversation.append({role: "user", content: input})
2. inner `while True` agentic tool loop: 
2a. execute_llm_call(conversation) sends full conversation to Claude API, returns raw text string
2b. extract_tool_invocations(assistant_response) parses text for lines like: "tool: read_file({"filename": "foo.py"})", returns [(name, args_dict), ...]
2ci. if no tools were found: print response, append to conversation, break
2cii. if tools were found: call the tools to use them, append assistant message (which includes result of tool call) to conversation, then loop back to step 2.