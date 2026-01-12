from langgraph.graph import StateGraph, END
from typing import Callable, Dict, Any
from .state_schema import AgentState

class Engine:
    """
    LangGraph compilation logic
    """
    def __init__(self):
        self.builder = StateGraph(AgentState)

    def add_node(self, name: str, node: Callable):
        self.builder.add_node(name, node)

    def add_edge(self, start_key: str, end_key: str):
        self.builder.add_edge(start_key, end_key)
        
    def set_entry_point(self, key: str):
        self.builder.set_entry_point(key)
        
    def add_conditional_edges(self, source: str, path: Callable):
        self.builder.add_conditional_edges(source, path)

    def compile(self):
        return self.builder.compile()
