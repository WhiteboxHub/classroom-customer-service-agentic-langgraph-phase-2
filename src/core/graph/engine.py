"""
LangGraph Engine: Complete execution graph with all nodes and conditional routing.
This is the execution engine that controls all flow - LLMs never control flow directly.
"""
from langgraph.graph import StateGraph, END
from typing import Callable, Dict, Any, Literal
from .state_schema import AgentState


class Engine:
    """
    LangGraph compilation and execution engine.
    
    Architectural rules:
    - Graph controls all execution flow
    - LLMs generate plans/suggestions but never control flow
    - All state transitions are explicit
    """
    
    def __init__(self):
        self.builder = StateGraph(AgentState)
        self._nodes_added = False
    
    def add_node(self, name: str, node: Callable):
        """Add a node to the graph."""
        self.builder.add_node(name, node)
    
    def add_edge(self, start_key: str, end_key: str):
        """Add a direct edge between nodes."""
        self.builder.add_edge(start_key, end_key)
    
    def set_entry_point(self, key: str):
        """Set the entry point of the graph."""
        self.builder.set_entry_point(key)
    
    def add_conditional_edges(
        self, source: str, path: Callable, path_map: Dict[str, str] = None
    ):
        """
        Add conditional edges with routing logic.
        
        Args:
            source: Source node name
            path: Function that returns next node name
            path_map: Optional mapping of return values to node names
        """
        if path_map:
            self.builder.add_conditional_edges(source, path, path_map)
        else:
            self.builder.add_conditional_edges(source, path)
    
    def build_complete_graph(
        self,
        orchestrator_node: Callable,
        claims_node: Callable,
        billing_node: Callable,
        scheduling_node: Callable,
        sentinel_node: Callable,
    ):
        """
        Build the complete execution graph with all nodes and edges.
        
        Graph structure:
        1. orchestrator -> (claims|billing|scheduling|__end__)
        2. claims -> sentinel -> __end__
        3. billing -> sentinel -> __end__
        4. scheduling -> sentinel -> __end__
        
        Sentinel has veto power - can end execution early.
        """
        # Add all nodes
        self.builder.add_node("orchestrator", orchestrator_node)
        self.builder.add_node("claims", claims_node)
        self.builder.add_node("billing", billing_node)
        self.builder.add_node("scheduling", scheduling_node)
        self.builder.add_node("sentinel", sentinel_node)
        
        # Set entry point
        self.builder.set_entry_point("orchestrator")
        
        # Orchestrator routes to domain agents
        def route_from_orchestrator(state: AgentState) -> Literal["claims", "billing", "scheduling", "__end__"]:
            """Route from orchestrator to domain agent or end."""
            next_step = state.get("next_step")
            if next_step in ["claims", "billing", "scheduling"]:
                return next_step
            return "__end__"
        
        self.builder.add_conditional_edges(
            "orchestrator",
            route_from_orchestrator,
            {
                "claims": "claims",
                "billing": "billing",
                "scheduling": "scheduling",
                "__end__": END,
            },
        )
        
        # Domain agents route to sentinel
        self.builder.add_edge("claims", "sentinel")
        self.builder.add_edge("billing", "sentinel")
        self.builder.add_edge("scheduling", "sentinel")
        
        # Sentinel routes to end (or could route back if needed)
        def route_from_sentinel(state: AgentState) -> Literal["__end__"]:
            """Route from sentinel - always end (sentinel can veto)."""
            # If sentinel vetoed, execution ends
            # If sentinel approved, execution also ends (domain agent already responded)
            return "__end__"
        
        self.builder.add_conditional_edges(
            "sentinel",
            route_from_sentinel,
            {"__end__": END},
        )
        
        self._nodes_added = True
    
    def compile(self):
        """
        Compile the graph for execution.
        
        Returns:
            Compiled LangGraph application
        """
        if not self._nodes_added:
            raise ValueError(
                "Graph not built. Call build_complete_graph() first or add nodes manually."
            )
        return self.builder.compile()
