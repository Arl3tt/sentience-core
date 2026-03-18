"""
LangGraph-based workflow runner for Sentience Core
Implements a robust graph-based orchestration with memory context integration
"""
try:
    import yaml
except Exception:
    yaml = None  # type: ignore
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import logging
from pathlib import Path

import importlib
try:
    _mod = importlib.import_module('langchain_core.messages')
    BaseMessage = getattr(_mod, 'BaseMessage')
    HumanMessage = getattr(_mod, 'HumanMessage')
    AIMessage = getattr(_mod, 'AIMessage')

    _prom = importlib.import_module('langchain_core.prompts')
    BasePromptTemplate = getattr(_prom, 'BasePromptTemplate')
    ChatPromptTemplate = getattr(_prom, 'ChatPromptTemplate')

    _run = importlib.import_module('langchain_core.runnables')
    RunnableConfig = getattr(_run, 'RunnableConfig')

    _lg = importlib.import_module('langgraph.graph')
    StateGraph = getattr(_lg, 'StateGraph')
    END = getattr(_lg, 'END')
except Exception:
    # Provide minimal runtime fallbacks so the module can be imported in test environments
    class BaseMessage:  # type: ignore
        pass

    class HumanMessage(BaseMessage):  # type: ignore
        def __init__(self, content=''):
            self.content = content

    class AIMessage(BaseMessage):  # type: ignore
        def __init__(self, content=''):
            self.content = content

    BasePromptTemplate = object
    ChatPromptTemplate = object
    RunnableConfig = object

    class StateGraph:  # type: ignore
        def __init__(self, state_schema=None):
            pass

        def add_node(self, *a, **k):
            pass

        def add_edge(self, *a, **k):
            pass

        def set_entry_point(self, p):
            pass

        def compile(self):
            return self

        def invoke(self, state, config=None):
            return state

    END = object()

from memory.memory_controller import semantic_search, store_memory, get_recent_neural_context
from policies.neuro_policy import neuro_policy
from core.agents import call_llm

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Maintains context and state for an agent node"""
    name: str
    memory_k: int = 4
    chat_history: List[BaseMessage] = field(default_factory=list)
    last_memory_query: Optional[str] = None
    verbosity: int = 2  # 0=minimal, 1=normal, 2=verbose
    allowed_actions: List[str] = field(default_factory=list)
    max_retries: int = 3
    retry_delay: float = 1.0

    def get_context(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant context from memory"""
        self.last_memory_query = query
        return semantic_search(query, top_k=self.memory_k)

    def store_result(self, content: str, metadata: Dict[str, Any]) -> None:
        """Store agent outputs in memory"""
        store_memory(content, metadata)

    def add_message(self, message: BaseMessage) -> None:
        """Add message to chat history"""
        self.chat_history.append(message)


class SentienceWorkflow:
    """Main workflow orchestrator using LangGraph"""

    def __init__(self, workflow_path: Optional[Union[str, Path]] = None):
        """Initialize workflow from YAML config"""
        if not workflow_path:
            workflow_path = Path(__file__).parent / "config" / "workflow.yaml"

        # ensure PyYAML is available and load the workflow with explicit encoding
        if yaml is None:
            raise RuntimeError(
                "PyYAML is required to load workflow YAML. Install it into your environment: `pip install pyyaml`"
            )

        if isinstance(workflow_path, Path):
            workflow_path = str(workflow_path)

        with open(workflow_path, 'r', encoding='utf-8') as f:
            self.config: Dict[str, Any] = yaml.safe_load(f)

        self.agents: Dict[str, AgentContext] = {}
        self._init_agents()
        self.graph = self._build_graph()

    def _init_agents(self):
        """Initialize agent contexts from config"""
        for name, cfg in self.config["nodes"].items():
            self.agents[name] = AgentContext(
                name=name,
                memory_k=cfg["config"].get("memory_query_k", 4)
            )

    def _build_graph(self) -> StateGraph:
        """Construct LangGraph workflow"""
        from typing import TypedDict

        class AgentState(TypedDict):
            agent: str
            result: str
            inputs: dict

        # Create the graph with state schema
        workflow = StateGraph(state_schema=AgentState)

        # Add agent nodes
        for name, agent in self.agents.items():
            workflow.add_node(name, self._create_agent_node(name, agent))

        # Add edges
        for edge in self.config["edges"]:
            workflow.add_edge(edge["from"], edge["to"])

        # Set entry/exit
        workflow.set_entry_point(self.config["entry_point"])
        workflow.add_edge(self.config["exit_point"], END)

        return workflow.compile()

    def _create_agent_node(self, name: str, context: AgentContext):
        """Create an agent node with memory context integration"""

        def agent_fn(state):
            # Get relevant context from state
            query = state.get("query", "")
            if not query and "task" in state:
                query = state["task"].get("desc", state["task"].get("title", ""))

            # inject recent neural context (Mode A)
            try:
                neural_ctx = get_recent_neural_context()
            except Exception:
                neural_ctx = None
            # attach neural context to state for visibility in prompts and middleware
            if neural_ctx is not None:
                state = {**state, "neural": neural_ctx}

            context_hits = context.get_context(query)

            # Build prompt with context
            prompt = self._build_prompt(name, context_hits, state)

            # Call agent
            result = call_llm(prompt)

            # Store result
            context.store_result(
                result,
                {"agent": name, "state": state, "context_hits": [h["id"] for h in context_hits]}
            )

            # Run policy and update agent context (Mode B) if neural context present
            try:
                neural_for_policy = state.get("neural")
                if neural_for_policy is not None:
                    policy_decision = neuro_policy(neural_for_policy)
                    # Persist policy decision as memory marker
                    try:
                        store_memory(f"neuro.policy:{policy_decision.get('action')}", {"policy": policy_decision})
                    except Exception:
                        pass

                    # Update agent context based on policy
                    action = policy_decision.get('action', 'neutral')
                    if action == 'protect_flow':
                        context.verbosity = 0  # minimal interruptions
                        context.max_retries = 1  # avoid repeated attempts
                    elif action == 'simplify':
                        context.verbosity = 1  # reduced output
                        context.allowed_actions = ['query', 'respond']  # limit complexity
                    elif action == 'cue_anti_drowsy':
                        context.verbosity = 2  # full engagement
                        context.retry_delay = 0.5  # faster responses
                    else:  # neutral
                        context.verbosity = 2
                        context.max_retries = 3
                        context.retry_delay = 1.0
                        context.allowed_actions = []  # no restrictions

                    # Attach policy decision to returned state
                    result_state = {
                        **state,
                        "agent": name,
                        "result": result,
                        "neuro_policy": policy_decision,
                        "agent_context": {
                            "verbosity": context.verbosity,
                            "max_retries": context.max_retries,
                            "retry_delay": context.retry_delay,
                            "allowed_actions": context.allowed_actions
                        }
                    }
                else:
                    result_state = {**state, "agent": name, "result": result}
            except Exception as e:
                log.warning(f"Policy update failed: {str(e)}")
                result_state = {**state, "agent": name, "result": result}

            # Update conversation history
            context.add_message(HumanMessage(content=prompt))
            context.add_message(AIMessage(content=result))

            # Return the new state (may include neuro_policy decision)
            return result_state

        return agent_fn

    def _build_prompt(self, agent_name: str, context_hits: List[Dict], inputs: Dict) -> str:
        """Build agent prompt with memory context"""
        prompt = f"\nYou are the {agent_name} agent. "

        if context_hits:
            prompt += "\nRelevant context:\n"
            for hit in context_hits:
                prompt += f"- {hit['text'][:200]}...\n"

        # Include neural summary if present in inputs
        neural = inputs.get("neural") if isinstance(inputs, dict) else None
        if neural:
            try:
                summary = neural.get("summary")
                avg_emb = neural.get("avg_embedding")
                prompt += "\nNeural context summary:\n"
                prompt += f"- sessions_used: {summary.get('count', 0)}\n"
                prompt += f"- latest_session: {summary.get('latest')}\n"
                # include embedding size if available
                if isinstance(avg_emb, (list, tuple)):
                    prompt += f"- avg_embedding_len: {len(avg_emb)}\n"
                elif hasattr(avg_emb, 'shape'):
                    try:
                        prompt += f"- avg_embedding_len: {avg_emb.shape[0]}\n"
                    except Exception:
                        pass
            except Exception:
                # best-effort include; ignore on failure
                pass

        # Inject policy-driven instructions if a neuro policy decision is present
        try:
            policy = None
            if isinstance(inputs, dict):
                policy = inputs.get('neuro_policy')
                if policy is None:
                    neural_block = inputs.get('neural')
                    if isinstance(neural_block, dict):
                        policy = neural_block.get('policy')
            if isinstance(policy, dict):
                action = policy.get('action')
            elif isinstance(policy, str):
                action = policy
            else:
                action = None

            ACTION_INSTRUCTIONS = {
                'protect_flow': 'Minimize interruptions, be concise, and avoid asking unnecessary questions.',
                'cue_anti_drowsy': 'Provide a brief alertness cue or suggestion to increase wakefulness.',
                'simplify': 'Simplify language and reduce cognitive load; prefer short sentences.',
                'neutral': 'Proceed normally.'
            }

            if action in ACTION_INSTRUCTIONS:
                prompt += "\nPolicy instruction:\n"
                prompt += f"- {ACTION_INSTRUCTIONS[action]}\n"
        except Exception:
            pass

        prompt += "\nCurrent inputs:\n"
        for k, v in inputs.items():
            prompt += f"{k}: {str(v)[:200]}...\n"

        prompt += f"\nAs the {agent_name}, what actions should be taken? Respond in a clear, structured format."
        return prompt

    def run(self, goal: str, config: Optional[Dict] = None) -> Dict[str, Any]:
        """Run the full workflow"""
        config = config or {}

        try:
            # Store the initial goal
            store_memory(
                f"New workflow run started with goal: {goal}",
                {"kind": "workflow.start", "goal": goal}
            )

            # Execute graph with initial state
            initial_state = {
                "agent": "start",
                "result": "",
                "inputs": {"query": goal}
            }
            result = self.graph.invoke(
                initial_state,
                config=config
            )

            # Store final result
            store_memory(
                f"Workflow completed. Final result: {str(result)[:200]}",
                {"kind": "workflow.complete", "goal": goal}
            )

            return result

        except Exception as e:
            log.exception("Workflow error")
            store_memory(
                f"Workflow error: {str(e)}",
                {"kind": "workflow.error", "goal": goal}
            )
            raise
