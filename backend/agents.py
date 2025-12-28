import os
import json
import asyncio
from typing import AsyncGenerator, List, Dict, Any, Optional
from groq import AsyncGroq
from .tools import TOOL_DEFINITIONS, AVAILABLE_TOOLS

# Predefined System Prompts
AGENT_PROMPTS = {
    "Researcher": (
        "You are a Senior Researcher. Your goal is to find accurate, comprehensive information. "
        "Use the 'web_search' tool to find information. "
        "Cite sources or explain your reasoning clearly."
    ),
    "Writer": (
        "You are a Professional Tech Writer. Your goal is to simplify complex topics. "
        "Use the provided research to write clear, engaging, and well-structured content. "
        "Focus on flow, readability, and impactful headings. "
        "If you see a 'HANDOFF_TO:Critic' command, ignore it in your output but prepare the text for review."
    ),
    "Critic": (
        "You are a Strict Editor/Critic. Your goal is to ensure quality. "
        "Review the provided content for logical errors, tone inconsistencies, and clarity. "
        "Provide constructive feedback and a revised version if necessary. "
        "Be concise and professional."
    ),
    "Coder": (
        "You are a Senior Software Engineer. Your goal is to write clean, efficient, and error-free code. "
        "Use 'web_search' if you need to look up documentation. "
        "Provide full implementations, not just snippets. "
        "Prefer Python/FastAPI/JavaScript unless specified otherwise."
    )
}

class Agent:
    def __init__(self, name: str, system_prompt: str = "", model: str = "llama3-70b-8192", tools: List[str] = None):
        self.name = name
        self.system_prompt = system_prompt or AGENT_PROMPTS.get(name, "You are a helpful AI assistant.")
        self.model = model
        self.client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
        
        # Filter available tools based on config
        # For this demo, Researcher and Coder get all tools by default
        if name in ["Researcher", "Coder", "Agent"]:
            self.tools = TOOL_DEFINITIONS
        else:
            self.tools = None # Writer/Critic usually don't need tools in this flow

    async def run_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, str], None]:
        """
        Stream response from Groq. Handles tool calls internally.
        """
        current_messages = [{"role": "system", "content": self.system_prompt}] + messages
        
        while True:
            try:
                # 1. Call LLM
                response_stream = await self.client.chat.completions.create(
                    messages=current_messages,
                    model=self.model,
                    tools=self.tools if self.tools else None,
                    tool_choice="auto" if self.tools else None,
                    stream=True,
                    temperature=0.7,
                    max_tokens=2048
                )

                tool_calls = []
                current_text_content = ""
                
                async for chunk in response_stream:
                    # Capture content
                    content = chunk.choices[0].delta.content
                    if content:
                        current_text_content += content
                        yield {
                            "type": "thought",
                            "text": content,
                            "agent": self.name
                        }
                    
                    # Capture tool calls (accumulate chunks)
                    if chunk.choices[0].delta.tool_calls:
                        for tc in chunk.choices[0].delta.tool_calls:
                            if len(tool_calls) <= tc.index:
                                tool_calls.append({
                                    "id": tc.id,
                                    "type": tc.type,
                                    "function": {"name": "", "arguments": ""}
                                })
                            
                            # Append name (often only in first chunk)
                            if tc.function.name:
                                tool_calls[tc.index]["function"]["name"] += tc.function.name
                            # Append arguments
                            if tc.function.arguments:
                                tool_calls[tc.index]["function"]["arguments"] += tc.function.arguments

                # If we have textual content, add it to history
                if current_text_content:
                    current_messages.append({"role": "assistant", "content": current_text_content})

                # 2. Process Tool Calls
                if tool_calls:
                    # Add tool calls to history
                    current_messages.append({
                        "role": "assistant",
                        "tool_calls": tool_calls, 
                        # content must be null if tool_calls is present? 
                        # Actually Groq/OpenAI allows content + tool_calls. 
                        # We already appended content above if it existed, but `tool_calls` message 
                        # might need to be separate or combined. 
                        # Standard Practice: One message with both if both present, or separate.
                        # Let's replace the last message if we just added content, or append new one?
                        # Simplification: Append a new message strictly for tool calls if needed, 
                        # but standard API expects the `tool_calls` field on the *assistant* message.
                        # So if we had content, we should merge.
                        # Let's rebuild the last message properly.
                    })
                    
                    # Fix history: Pop the content-only message if we added it, replace with combined
                    if current_text_content:
                        current_messages.pop()
                    
                    current_messages.append({
                        "role": "assistant",
                        "content": current_text_content, # can be None/empty
                        "tool_calls": tool_calls
                    })

                    # Execute loop
                    for tc in tool_calls:
                        fn_name = tc["function"]["name"]
                        args_str = tc["function"]["arguments"]
                        
                        yield {
                            "type": "info", # Or 'tool_start'
                            "text": f"\n[Executing tool: {fn_name}({args_str})]\n",
                            "agent": self.name
                        }
                        
                        try:
                            args = json.loads(args_str)
                            tool_fn = AVAILABLE_TOOLS.get(fn_name)
                            
                            if tool_fn:
                                result = tool_fn(**args)
                            else:
                                result = f"Error: Tool {fn_name} not found."
                                
                        except Exception as e:
                            result = f"Error executing tool: {str(e)}"
                        
                        # Yield result status (optional, maybe too verbose to show full JSON)
                        # yield {
                        #     "type": "info", 
                        #     "text": f"\n[Tool Result: {str(result)[:50]}...]\n", 
                        #     "agent": self.name
                        # }

                        # Append tool output to history
                        current_messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "name": fn_name,
                            "content": str(result)
                        })

                    # Loop continues to next iteration to let LLM process tool results
                    continue
                
                else:
                    # No tool calls, we are done with this turn
                    break

            except Exception as e:
                yield {
                    "type": "error",
                    "text": f"Error in agent loop: {str(e)}",
                    "agent": self.name
                }
                break
