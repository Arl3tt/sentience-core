"""
BCI Tools Integration Example for Agent System

This example shows how to integrate the new BCI tools with your existing agent system.
Add these to your core/agents.py or create separate tool handlers.
"""

# Example 1: Integrate into Executor Agent
# ==========================================

def execute_bci_analysis_task(task_description: str, eeg_data: np.ndarray, fs: float = 250):
    """
    Execute a BCI analysis task in the Executor agent
    Can be called from executor's LLM-based action proposal
    """
    from core.tools import (
        classify_brainwave_bands,
        classify_motor_imagery,
        create_hybrid_bci
    )
    
    if "brain waves" in task_description.lower():
        return classify_brainwave_bands(eeg_data, fs)
    
    elif "motor imagery" in task_description.lower():
        return classify_motor_imagery(eeg_data, fs)
    
    elif "bci" in task_description.lower() or "hybrid" in task_description.lower():
        bci = create_hybrid_bci()
        return bci.process_multi_paradigm(eeg_data, fs)
    
    return {"status": "task_not_recognized"}


# Example 2: Memory Integration
# ==============================

def store_bci_result_in_memory(analysis_result: dict):
    """Store BCI analysis results in the memory system"""
    from memory.memory_controller import store_memory
    import json
    
    store_memory(json.dumps(analysis_result), {"kind": "bci_analysis"})


def retrieve_bci_history():
    """Retrieve historical BCI analyses"""
    from memory.memory_controller import semantic_search
    
    history = semantic_search("bci analysis", top_k=10)
    return history


# Example 3: Add to Tool Runner
# =============================

def extend_tool_runner_with_bci():
    """
    Extend core/tools/tool_runner.py with BCI support
    Add this to the existing tool_runner.py
    """
    
    def run_bci_analysis(analysis_type: str, eeg_data, **kwargs):
        """Run BCI analysis"""
        from core.tools import (
            classify_brainwave_bands,
            classify_cognitive_state,
            classify_motor_imagery,
            classify_p300_response,
            create_neurofeedback_session,
            create_hybrid_bci,
            create_asd_analyzer
        )
        
        fs = kwargs.get("fs", 250)
        
        analysis_map = {
            "brain_waves": lambda: classify_brainwave_bands(eeg_data, fs),
            "cognitive_state": lambda: classify_cognitive_state(eeg_data, fs),
            "motor_imagery": lambda: classify_motor_imagery(eeg_data, fs),
            "p300": lambda: classify_p300_response(eeg_data, fs),
            "hybrid_bci": lambda: create_hybrid_bci().process_multi_paradigm(eeg_data, fs),
            "asd_analysis": lambda: create_asd_analyzer().analyze_attention_profile(
                eeg_data, 
                kwargs.get("duration", 1.0),
                kwargs.get("context", "neutral")
            ),
        }
        
        if analysis_type in analysis_map:
            return analysis_map[analysis_type]()
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}


# Example 4: Researcher Agent Enhancement
# =========================================

def enhance_researcher_with_bci_context(task_description: str):
    """
    Enhance Researcher agent to find BCI-relevant context
    """
    from memory.memory_controller import semantic_search
    
    bci_queries = [
        "EEG signal processing",
        "motor imagery classification",
        "P300 detection",
        "neurofeedback",
        "BCI paradigms",
        "attention analysis"
    ]
    
    for query in bci_queries:
        if any(keyword in task_description.lower() for keyword in query.split()):
            context = semantic_search(query, top_k=3)
            return context
    
    return []


# Example 5: Critic Agent with BCI Evaluation
# ============================================

def evaluate_bci_result(analysis_result: dict) -> dict:
    """
    Evaluate BCI analysis results in Critic agent
    """
    evaluation = {
        "result_quality": "good" if analysis_result.get("confidence", 0) > 0.7 else "needs_review",
        "confidence_score": analysis_result.get("confidence", 0),
        "next_steps": []
    }
    
    # Determine next steps based on result
    if "predicted_imagery" in analysis_result:
        evaluation["next_steps"].append("Execute motor imagery command")
    
    if "contains_p300" in analysis_result and analysis_result.get("contains_p300"):
        evaluation["next_steps"].append("Process P300 and select character")
    
    if "asd_likelihood" in analysis_result:
        score = analysis_result["asd_likelihood"]["score"]
        if score > 0.6:
            evaluation["next_steps"].append("Recommend clinical assessment")
    
    return evaluation


# Example 6: Real-time Feedback Loop
# ===================================

class RealTimeBCIAgent:
    """Agent that provides real-time BCI feedback"""
    
    def __init__(self):
        from core.tools import create_neurofeedback_session
        self.neurofeedback = create_neurofeedback_session(
            target="relaxation",
            modality="visual"
        )
        # Register callback to process feedback
        self.neurofeedback.add_feedback_callback(self.handle_feedback)
    
    def handle_feedback(self, feedback, metrics):
        """Handle neurofeedback in real-time"""
        from ui.voice import speak
        from memory.memory_controller import store_memory
        import json
        
        # Store feedback
        store_memory(json.dumps(feedback), {"kind": "neurofeedback"})
        
        # Provide audio cues
        if feedback["level"] == "excellent":
            speak("Great focus!")
        elif feedback["level"] == "good":
            speak("Keep going")
    
    def process_chunk(self, eeg_chunk):
        """Process EEG chunk with feedback"""
        return self.neurofeedback.process_eeg_chunk(eeg_chunk)


# Example 7: Goal Decomposition with BCI
# =======================================

def decompose_bci_goal(goal: str) -> list:
    """
    Decompose high-level BCI goals into tasks
    Returns JSON task list for Planner agent
    """
    goal_lower = goal.lower()
    
    if "spell" in goal_lower or "p300" in goal_lower:
        return [
            {
                "title": "Initialize P300 Speller",
                "desc": "Set up P300-based speller interface",
                "estimate_hours": 0.5
            },
            {
                "title": "Process P300 Sequences",
                "desc": "Run P300 detection on trial sequences",
                "estimate_hours": 1.0
            },
            {
                "title": "Evaluate Results",
                "desc": "Analyze spelling accuracy and SNR",
                "estimate_hours": 0.5
            }
        ]
    
    elif "imagery" in goal_lower or "motor" in goal_lower:
        return [
            {
                "title": "Preprocess Motor Imagery Data",
                "desc": "Filter and normalize EEG for motor imagery",
                "estimate_hours": 0.5
            },
            {
                "title": "Classify Motor Imagery",
                "desc": "Identify left/right hand, feet, or tongue imagery",
                "estimate_hours": 1.0
            },
            {
                "title": "Execute Motor Command",
                "desc": "Convert imagery classification to BCI command",
                "estimate_hours": 0.5
            }
        ]
    
    elif "focus" in goal_lower or "attention" in goal_lower:
        return [
            {
                "title": "Analyze Attention State",
                "desc": "Classify cognitive state and attention level",
                "estimate_hours": 0.5
            },
            {
                "title": "Provide Neurofeedback",
                "desc": "Generate real-time feedback to improve focus",
                "estimate_hours": 1.0
            },
            {
                "title": "Report Results",
                "desc": "Summarize attention metrics and improvements",
                "estimate_hours": 0.5
            }
        ]
    
    elif "asd" in goal_lower or "autism" in goal_lower:
        return [
            {
                "title": "Initialize ASD Analyzer",
                "desc": "Set up attention analysis for ASD patterns",
                "estimate_hours": 0.5
            },
            {
                "title": "Analyze Attention Profile",
                "desc": "Detect ASD-related attention characteristics",
                "estimate_hours": 1.0
            },
            {
                "title": "Generate Report",
                "desc": "Provide recommendations and longitudinal tracking",
                "estimate_hours": 0.5
            }
        ]
    
    # Default: hybrid BCI
    return [
        {
            "title": "Initialize Hybrid BCI",
            "desc": "Set up multi-paradigm BCI system",
            "estimate_hours": 0.5
        },
        {
            "title": "Process Multi-Modal EEG",
            "desc": "Analyze through motor imagery, P300, and SSVEP",
            "estimate_hours": 1.0
        },
        {
            "title": "Fuse Results",
            "desc": "Combine paradigm outputs with weighted voting",
            "estimate_hours": 0.5
        }
    ]


# Example 8: Integration with Planner
# ====================================

def enhance_planner_with_bci():
    """
    Modify core/agents.py Planner class to handle BCI goals
    """
    
    # In Planner.run() method, add:
    
    # Detect if goal is BCI-related
    if any(keyword in goal.lower() for keyword in 
           ["bci", "eeg", "brain", "imagery", "p300", "speller", 
            "neurofeedback", "attention", "asd", "cognitive"]):
        
        # Use BCI-specific task decomposition
        tasks = decompose_bci_goal(goal)
        
        for task in tasks:
            # Store with BCI context
            task["context"] = "bci_analysis"
            self.task_q.put(task)


# ==================================================
# Usage in your existing agent system
# ==================================================

# 1. Add imports to core/agents.py
import sys
sys.path.insert(0, '/path/to/sentience-core')
from core.tools import (
    classify_brainwave_bands,
    classify_motor_imagery,
    create_hybrid_bci,
    create_neurofeedback_session,
    analyze_asd_attention
)

# 2. Register BCI tasks in Executor
# Modify Executor.run() to call:
result = execute_bci_analysis_task(task_desc, eeg_data, fs=250)
store_bci_result_in_memory(result)

# 3. Add BCI context to Researcher
# Modify Researcher.run() to call:
bci_context = enhance_researcher_with_bci_context(task_desc)

# 4. Evaluate BCI results in Critic
# Modify Critic.run() to call:
evaluation = evaluate_bci_result(result)

# ==================================================
# Benefits
# ==================================================

"""
✓ Seamless agent integration with BCI capabilities
✓ Memory-based learning from BCI analyses
✓ Real-time neurofeedback with callbacks
✓ Multi-paradigm BCI for robust commands
✓ Clinical-grade ASD attention analysis
✓ Automatic task decomposition for BCI goals
✓ Performance evaluation and improvement tracking
✓ Full compatibility with existing agent system
"""
