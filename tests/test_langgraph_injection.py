import sys
import types

# Create minimal dummy modules for heavy dependencies so importing the runner succeeds
lc = types.ModuleType('langchain_core')
lc_messages = types.ModuleType('langchain_core.messages')
lc_prompts = types.ModuleType('langchain_core.prompts')
lc_runnables = types.ModuleType('langchain_core.runnables')
setattr(lc_prompts, 'BasePromptTemplate', object)
setattr(lc_prompts, 'ChatPromptTemplate', object)
setattr(lc_runnables, 'RunnableConfig', object)

class HumanMessage:
    def __init__(self, content=''):
        self.content = content

class AIMessage:
    def __init__(self, content=''):
        self.content = content

setattr(lc_messages, 'HumanMessage', HumanMessage)
setattr(lc_messages, 'AIMessage', AIMessage)
setattr(lc_messages, 'BaseMessage', object)

sys.modules['langchain_core'] = lc
sys.modules['langchain_core.messages'] = lc_messages
sys.modules['langchain_core.prompts'] = lc_prompts
sys.modules['langchain_core.runnables'] = lc_runnables

# Dummy langgraph.graph with minimal API (not used in this test)
lg_mod = types.ModuleType('langgraph.graph')
class DummyStateGraph:
    def __init__(self, state_schema=None):
        pass
    def add_node(self, name, fn):
        pass
    def add_edge(self, a, b):
        pass
    def set_entry_point(self, p):
        pass
    def compile(self):
        class C:
            def invoke(self, state, config=None):
                return state
        return C()

setattr(lg_mod, 'StateGraph', DummyStateGraph)
setattr(lg_mod, 'END', object())
sys.modules['langgraph'] = types.ModuleType('langgraph')
sys.modules['langgraph.graph'] = lg_mod

# Provide a lightweight yaml module to avoid installing PyYAML in tests
sys.modules['yaml'] = types.ModuleType('yaml')

# Provide a dummy openai module to satisfy core.agents imports
sys.modules['openai'] = types.ModuleType('openai')

# Provide a lightweight stub for core.agents to avoid initializing OpenAI client
core_agents_stub = types.ModuleType('core.agents')
def _call_llm_stub(prompt, max_tokens=600, temp=0.2):
    return "[LLM stub response]"
setattr(core_agents_stub, 'call_llm', _call_llm_stub)
prev_core_agents = sys.modules.get('core.agents')
sys.modules['core.agents'] = core_agents_stub

# Now import the runner, then restore any previous core.agents entry
try:
    from core.langgraph_runner import SentienceWorkflow
finally:
    if prev_core_agents is None:
        del sys.modules['core.agents']
    else:
        sys.modules['core.agents'] = prev_core_agents


def test_prompt_includes_neural_and_policy():
    # Build a fake inputs dict with neural summary and a policy decision
    inputs = {'query': 'Test question',
        'neural': {'summary': {'count': 2, 'latest': 'session_1'},
            'avg_embedding': [0.0] * 16},
        'neuro_policy': {'action': 'protect_flow'}}

    # Instantiate a workflow shell and call _build_prompt
    wf = SentienceWorkflow.__new__(SentienceWorkflow)
    prompt = SentienceWorkflow._build_prompt(wf, 'TestAgent', [], inputs)

    assert 'Neural context summary' in prompt
    assert 'Policy instruction' in prompt
    assert 'Minimize interruptions' in prompt
