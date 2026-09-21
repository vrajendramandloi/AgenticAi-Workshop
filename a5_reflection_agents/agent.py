import json
import os
import urllib.parse
import urllib.request
from google.adk.agents import LoopAgent, LlmAgent, SequentialAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.callback_context import CallbackContext

try:
    from instructions import (
        CRITIC_AGENT_INSTRUCTION,
        COMPLETION_PHRASE,
        STATE_CRITICISM,
        STATE_CURRENT_DOC,
        INITIAL_WRITER_AGENT_INSTRUCTIONS,
        REFINE_AGENT_LOOP_INSTRUCTIONS,
    )
except ImportError:
    from .instructions import (
        CRITIC_AGENT_INSTRUCTION,
        COMPLETION_PHRASE,
        STATE_CRITICISM,
        STATE_CURRENT_DOC,
        INITIAL_WRITER_AGENT_INSTRUCTIONS,
        REFINE_AGENT_LOOP_INSTRUCTIONS,
    )


from pathlib import Path

try:
    from dotenv import load_dotenv, find_dotenv
    # Explicitly load root workspace .env (d:\WORK\WORKSPACE\AI\.env)
    _root_env = Path(__file__).resolve().parent.parent / ".env"
    if _root_env.exists():
        load_dotenv(dotenv_path=_root_env)
    else:
        load_dotenv(find_dotenv())
    MODEL_NAME = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-3.5-flash-lite")
except ImportError:
    print("ERROR: Import Error while importing Model")

# --- State Keys ---
STATE_CURRENT_DOC = "current_document"
STATE_CRITICISM = "criticism"
# Define the exact phrase the Critic should use to signal completion
COMPLETION_PHRASE = "No major issues found."

# --- Tool Definition ---
def exit_loop(tool_context: ToolContext):
    """Call this function ONLY when the critique indicates no further changes are needed, signaling the iterative process should end."""
    print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    tool_context.actions.skip_summarization = True
    # Return empty dict as tools should typically return JSON-serializable output
    return {}

# --- Before Agent Callback ---
def update_initial_topic_state(callback_context: CallbackContext):
    """Ensure 'initial_topic' is set in state from the incoming user prompt."""
    user_txt = ""
    if getattr(callback_context, "user_content", None) and getattr(callback_context.user_content, "parts", None):
        user_txt = " ".join([p.text for p in callback_context.user_content.parts if getattr(p, "text", None)]).strip()
    
    if user_txt:
        callback_context.state['initial_topic'] = user_txt
    elif 'initial_topic' not in callback_context.state:
        callback_context.state['initial_topic'] = (
            "Objective: Move 3 police and 3 criminals across a river using a 2-person boat without anyone escaping.\n"
            "Conditions:\n"
            "1. Criminal cannot be sent alone in boat (they will escape via river).\n"
            "2. If criminals are left without any police on any shore they run away.\n"
            "3. All 3 criminals should safely cross the river."
        )

# --- Agent Definitions ---

# STEP 1: Initial Solver Agent (Proposes initial structured plan)
initial_writer_agent = LlmAgent(
    name="InitialSolverAgent",
    model=MODEL_NAME,
    include_contents='none',
    instruction=INITIAL_WRITER_AGENT_INSTRUCTIONS,
    description="Analyzes the problem objective and conditions to propose an initial step-by-step plan.",
    output_key=STATE_CURRENT_DOC
)

# STEP 2a: Critic Agent (Audits every move against user-defined conditions)
critic_agent_in_loop = LlmAgent(
    name="CriticAgent",
    model=MODEL_NAME,
    include_contents='none',
    instruction=CRITIC_AGENT_INSTRUCTION,
    description="Rigorously audits every single transition and state against all user conditions, rejecting invalid moves.",
    output_key=STATE_CRITICISM
)

# STEP 2b: Refiner Agent (Reconstructs plan, eliminates flaws, or triggers exit_loop)
refiner_agent_in_loop = LlmAgent(
    name="RefinerAgent",
    model=MODEL_NAME,
    include_contents='none',
    instruction=REFINE_AGENT_LOOP_INSTRUCTIONS,
    description="Refines the plan step-by-step based on the audit feedback, or calls exit_loop when approved.",
    tools=[exit_loop],
    output_key=STATE_CURRENT_DOC
)

# STEP 2: Refinement Loop Agent
refinement_loop = LoopAgent(
    name="RefinementLoop",
    sub_agents=[
        critic_agent_in_loop,
        refiner_agent_in_loop,
    ],
    max_iterations=5
)

# STEP 3: Overall Sequential Pipeline
root_agent = SequentialAgent(
    name="ConstraintReflectionPipeline",
    sub_agents=[
        initial_writer_agent,
        refinement_loop
    ],
    before_agent_callback=update_initial_topic_state,
    description="Generalized Constraint Reflection Pipeline: Generates initial plan, audits every step against stated conditions, and refines until verified."
)