# currently: client.chat.completions.create (2020)
# https://developers.openai.com/api/reference/resources/chat

# updated: client.responses.create from responses api (2025)
# https://developers.openai.com/api/reference/resources/responses 

import inspect
import json
import os
import anthropic

from dotenv import load_dotenv
from pathlib import Path
from typing import Any, Dict, List, Tuple

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_KEY"])
# openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

SYSTEM_PROMPT = """
You are a coding assistant whose goal it is to help me solve coding tasks. 
You have access to a series of tools you can execute. Here are the tools you can execute:

{tool_list_repr}

When you want to use a tool, reply with exactly one line in this exact format: 'tool: TOOL_NAME({{JSON_ARGS}})'.
Use compact single-line JSON with double quotes. After receiving a tool_result(...) message, continue the task.
If no tool is needed, respond normally.
"""

YOU_COLOR = "\u001b[94m"
ASSISTANT_COLOR = "\u001b[93m"
RESET_COLOR = "\u001b[0m"


def convert_to_full_path(path_str: str) -> Path:
    """
    exercises.py -> /Users/eq/GithubProjects/modern-software-dev-assignments/exercises.py
    """
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path

# three main functions
def read_file_tool(filename: str) -> Dict[str, Any]:
    pass
    # """
    # Gets the full content of a file provided by the user.
    # :param filename: The name of the file to read.
    # :return: The full content of the file.
    # """
    # full_path = convert_to_full_path(filename)
    # print(full_path)
    # with open(str(full_path), "r") as f:
    #     content = f.read()
    # return {
    #     "file_path": str(full_path),
    #     "content": content
    # }

def list_files_tool(path: str) -> Dict[str, Any]:
    pass
    # """
    # Lists the files in a directory provided by the user.
    # :param path: The path to a directory to list files from.
    # :return: A list of files in the directory.
    # """
    # full_path = convert_to_full_path(path)
    # all_files = []
    # for item in full_path.iterdir():
    #     all_files.append({
    #         "filename": item.name,
    #         "type": "file" if item.is_file() else "dir"
    #     })
    # return {
    #     "path": str(full_path),
    #     "files": all_files
    # }

def edit_file_tool(path: str, old_str: str, new_str: str) -> Dict[str, Any]:
    pass
    # """
    # Replaces first occurrence of old_str with new_str in file. If old_str is empty,
    # create/overwrite file with new_str.
    # :param path: The path to the file to edit.
    # :param old_str: The string to replace.
    # :param new_str: The string to replace with.
    # :return: A dictionary with the path to the file and the action taken.
    # """
    # full_path = convert_to_full_path(path)
    # if old_str == "":
    #     full_path.write_text(new_str, encoding="utf-8")
    #     return {
    #         "path": str(full_path),
    #         "action": "created_file"
    #     }
    # original = full_path.read_text(encoding="utf-8")
    # if original.find(old_str) == -1:
    #     return {
    #         "path": str(full_path),
    #         "action": "old_str not found"
    #     }
    # edited = original.replace(old_str, new_str, 1)
    # full_path.write_text(edited, encoding="utf-8")
    # return {
    #     "path": str(full_path),
    #     "action": "edited"
    # }
    
# tools
TOOL_REGISTRY = {
    "read_file": read_file_tool,
    "list_files": list_files_tool,
    "edit_file": edit_file_tool 
}

# take tool representation, return stringified representation
# reading built-in attributes to build human-readable description for prompt 
def get_tool_str_representation(tool_name: str) -> str:
    tool = TOOL_REGISTRY[tool_name]
    return f"""
    Name: {tool_name}
    Description: {tool.__doc__}
    Signature: {inspect.signature(tool)}
    """

# feed string representation to full system prompt
def get_full_system_prompt() -> str:
    tool_str_repr = ""
    for tool_name in TOOL_REGISTRY:
        tool_str_repr += "TOOL\n===" + get_tool_str_representation(tool_name)
        tool_str_repr += f"\n{"="*15}\n"
    return SYSTEM_PROMPT.format(tool_list_repr=tool_str_repr)

# receive output of LLM to execute tool
def extract_tool_invocations(text: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Return list of (tool_name, args) requested in 'tool: name({...})' lines.
    The parser expects single-line, compact JSON in parentheses.

    get_tool_str_representation() returns string
    \"""
    Name: read_file
    Description: <full content inputted by user>
    Signature: (filename: str) -> Dict[str, Any]
    \"""

    so calling it thrice will produce

    \"""
    TOOL
    ===
        Name: read_file
        Description: ...
        Signature: ...

    ===============
    \"""

    """
    invocations = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("tool:"):
            continue
        try:
            after = line[len("tool:"):].strip()
            name, rest = after.split("(", 1)
            name = name.strip()
            if not rest.endswith(")"):
                continue
            json_str = rest[:-1].strip()
            args = json.loads(json_str)
            invocations.append((name, args))
        except Exception as e:
            print(f"An exception occurred in extract_tool_invocations: {e}")
            break
    return invocations

# straightforward
def execute_llm_call(conversation: List[Dict[str, str]]) -> str:
    # response = openai_client.chat.completions.create(
    #     model="gpt-5",
    #     messages=conversation,
    #     max_completion_tokens=1000
    # )
    # return response.choices[0].message.content

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=get_full_system_prompt(),
        messages=conversation
    )
    return response.content[0].text

# core loop of the agent: run through the described sequence, to keep the conversation going
# 1: user prompts IDE. conversation = [prompt]
# 2. IDE sends prompt to LLM
# 3. LLM response (e.g.: list of tools). based on response:
#   if needed: append assistant message, execute tool, appent tool_result as "user". then loop back, send whole list again (now wth tool result)
#   if no tool needed: print answer, break inner loop
def run_coding_agent_loop():

    # good for debugging
    print(get_full_system_prompt())

    # init conversation object
    # keep track of conversations
    # standard formatting that most LLMs use
    # conversation = [{
    #     "role": "system",
    #     "content": get_full_system_prompt()
    # }]
    conversation = []

    # keep conversation running (wait for new user input each iteration)
    while True:
        try:
            user_input = input(f"{YOU_COLOR}You{RESET_COLOR}: ")
        # defensive programming: ctrl-C, D if we use it
        except (KeyboardInterrupt, EOFError) as e:
            print(f"An error occured in run_coding_agent_loop(): {e}")
            break

        conversation.append({
            "role": "user",
            "content": user_input.strip()
        })

        # handle LLM's agentic behavior for a single user message
        while True:
            assistant_response = execute_llm_call(conversation)
            tool_invocations = extract_tool_invocations(assistant_response)

            print(tool_invocations)
            
            # if no tools mentioned in the string
            if not tool_invocations:
                print(f"{ASSISTANT_COLOR}Assistant{RESET_COLOR}: {assistant_response}")
                conversation.append({
                    "role": "assistant",   # todo: del next block
                    "content": assistant_response
                })
                break

            # else: append and invoke tools
            print(f"{ASSISTANT_COLOR}Assistant{RESET_COLOR}: {assistant_response}")
            conversation.append({
                "role": "assistant",
                "content": assistant_response
            })

            for name, args in tool_invocations:
                # print(name, args)         # for debugging
                tool = TOOL_REGISTRY[name]  # the 3 KV pairs we defined
                resp = [] # ""
                # print(name, args)
                if name == "read_file":
                    print("READ FILE CALLED")
                    # resp = tool(args.get("filename", "."))
                elif name == "list_files":
                    print("LIST FILES CALLED")
                    # resp = tool(args.get("path", "."))
                elif name == "edit_file":
                    print("EDIT FILES CALLED")
                    resp = tool(args.get("path", "."),
                                args.get("old_str", ""),
                                args.get("new_str", ""))
                
            conversation.append({
                "role": "user",                                 # this time, it's user msg
                "content": f"tool_result({json.dumps(resp)})"   # TODO: fill `resp`
            })

if __name__ == "__main__":
    run_coding_agent_loop()
    