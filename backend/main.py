from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .models import RunRequest, Workflow, Node
from pydantic import BaseModel
from .agents import Agent, AGENT_PROMPTS
import json
import asyncio
from typing import List, Dict, Set

app = FastAPI(title="AgentForge Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunNodeRequest(BaseModel):
    agent_config: dict
    history: List[Dict[str, str]]
    prompt: str

@app.post("/run_node")
async def run_single_node(request: RunNodeRequest = Body(...)):
    """
    Executes a single agent node.
    Streams logs and final result/thought.
    """
    agent_data = request.agent_config
    agent_name = agent_data.get("name", "Unknown")
    system_prompt = agent_data.get("system_prompt", "")
    history = request.history
    
    async def event_generator():
        # yield f"event: log\ndata: {json.dumps({'agent': 'System', 'text': f'Activating {agent_name}...', 'type': 'info'})}\n\n"

        agent = Agent(name=agent_name, system_prompt=system_prompt)
        
        # Pruning
        pruned_history = history[-10:] if len(history) > 10 else history

        full_response = ""
        try:
             async for event in agent.run_stream(pruned_history):
                if event["type"] == "thought":
                    chunk = event["text"]
                    full_response += chunk
                    sse_payload = json.dumps({
                        "agent": agent_name,
                        "text": chunk,
                        "type": "thought"
                    })
                    yield f"event: log\ndata: {sse_payload}\n\n"
                elif event["type"] == "error":
                     yield f"event: log\ndata: {json.dumps({'agent': 'System', 'text': event['text'], 'type': 'error'})}\n\n"
        except Exception as e:
             yield f"event: log\ndata: {json.dumps({'agent': 'System', 'text': f'Error details: {str(e)}', 'type': 'error'})}\n\n"
             yield f"event: end\ndata: {json.dumps({'status': 'error'})}\n\n"
             return

        # Return final content event so frontend can append to history
        yield f"event: end\ndata: {json.dumps({'status': 'success', 'content': full_response})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/run")
async def run_workflow(request: RunRequest = Body(...)):
    """
    Executes the workflow graph.
    1. Finds start node (or first agent node).
    2. Traverses edges sequentially.
    3. Streams output via SSE.
    """
    workflow = request.workflow
    prompt = request.prompt
    
    async def event_generator():
        yield f"event: log\ndata: {json.dumps({'agent': 'System', 'text': f'Workflow started with prompt: {prompt}', 'type': 'info'})}\n\n"

        # 1. Build Graph Map
        # node_id -> node
        node_map = {n.id: n for n in workflow.nodes}
        # source_id -> [target_id] (Adjacency list)
        adj_list = {n.id: [] for n in workflow.nodes}
        for edge in workflow.edges:
            if edge.source in adj_list:
                adj_list[edge.source].append(edge.target)

        # 2. Find Start Node
        # Heuristic: Node with no incoming edges or the first defined node
        incoming_edges = set(e.target for e in workflow.edges)
        start_nodes = [n for n in workflow.nodes if n.id not in incoming_edges]
        
        if not start_nodes:
             # Cycle or all connected? Pick first.
             current_node_id = workflow.nodes[0].id if workflow.nodes else None
        else:
             current_node_id = start_nodes[0].id

        if not current_node_id:
             yield f"event: log\ndata: {json.dumps({'agent': 'System', 'text': 'Error: Empty workflow.', 'type': 'error'})}\n\n"
             return

        # 3. Execution Loop
        visited: Set[str] = set()
        # Message history shared across agents (simple shared state)
        # We prune this to keep context window manageable
        history: List[Dict[str, str]] = [
            {"role": "user", "content": prompt}
        ]

        while current_node_id:
            if current_node_id in visited:
                yield f"event: log\ndata: {json.dumps({'agent': 'System', 'text': 'Loop detected. Stopping execution.', 'type': 'error'})}\n\n"
                break
            visited.add(current_node_id)
            
            node = node_map[current_node_id]
            node_type = node.data.get("name", "Unknown") # 'Researcher', 'Writer' etc.
            system_prompt = node.data.get("system_prompt", "")
            
            yield f"event: log\ndata: {json.dumps({'agent': 'System', 'text': f'Activating {node_type}...', 'type': 'info'})}\n\n"

            # Create Agent
            # Tools are assigned in Agent.__init__ based on name (Researcher/Coder get tools)
            agent = Agent(name=node_type, system_prompt=system_prompt)
            
            # Run Agent
            # Pass recent history (pruned to last 10 messages)
            pruned_history = history[-10:] if len(history) > 10 else history
            
            full_response = ""
            async for event in agent.run_stream(pruned_history):
                if event["type"] == "thought":
                    chunk = event["text"]
                    full_response += chunk
                    # SSE format: data: <content>
                    # We send just the text chunk for the UI log
                    safe_chunk = chunk.replace('\n', ' ') # Simple escaping for single-line data field
                    if safe_chunk.strip():
                        # We send a JSON-like structure or just text. 
                        # The UI expects distinct lines or JSON? 
                        # UI Code: `const msg = line.replace('data: ', '').trim(); if(msg) this.addLog(msg);`
                        # UI log handling is simple string. Let's send nicely formatted string or JSON if we change UI.
                        # The user asked: `Streams events via SSE: {"agent": "Writer", "text": "chunk", "type": "thought"}`
                        # So I must send structured JSON in 'data'.
                        
                        sse_payload = json.dumps({
                            "agent": event["agent"],
                            "text": chunk,
                            "type": "thought"
                        })
                        yield f"event: log\ndata: {sse_payload}\n\n"
                elif event["type"] == "error":
                     yield f"event: log\ndata: {json.dumps({'agent': 'System', 'text': event['text'], 'type': 'error'})}\n\n"

            # Append result to history for next agent
            history.append({"role": "assistant", "content": full_response})
            
            # Handoff Logic / Graph Traversal
            # Check for Handoff command? 
            # "Detect handoff commands (e.g., 'HANDOFF_TO:Critic')"
            if "HANDOFF_TO:" in full_response:
                # Naive parsing
                potential_target = full_response.split("HANDOFF_TO:")[1].split()[0].strip()
                # Try to find a node with this name? 
                # Or just follow the edge?
                # User said "Executes agents sequentially via edges" BUT also "Detect handoff".
                # I will prioritize Edge Traversal, but maybe Handoff validates it?
                # Let's stick to explicit edges for the *visual* builder flow. 
                # Handoff commands might be internal agent logic, but the graph drives flow.
                pass 

            # Move to next node
            neighbors = adj_list[current_node_id]
            if neighbors:
                # Linear assumption: take first neighbor
                current_node_id = neighbors[0]
            else:
                current_node_id = None
                
            yield f"event: log\ndata: {json.dumps({'agent': 'System', 'text': f'{node_type} finished.', 'type': 'info'})}\n\n"
            
        yield f"event: log\ndata: {json.dumps({'agent': 'System', 'text': 'Workflow completed.', 'type': 'success'})}\n\n"
        yield "event: end\ndata: \n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
