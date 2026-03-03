import logging
from typing import List
from app.models.models import ChainNode, ChainEdge

logger = logging.getLogger(__name__)

class DAGEngine:
    """
    Engine to orchestrate Attack Chains.
    For Milestone 1, we just do a basic topological sort to determine execution order.
    """
    
    @staticmethod
    def get_execution_order(nodes: List[ChainNode], edges: List[ChainEdge]) -> List[ChainNode]:
        """
        Kahn's algorithm for topological sort.
        """
        # Node ID -> Node Map
        node_map = {node.id: node for node in nodes}
        
        # Adjacency list and in-degree counter
        adj_list = {node.id: [] for node in nodes}
        in_degree = {node.id: 0 for node in nodes}
        
        for edge in edges:
            if edge.source_node_id in adj_list and edge.target_node_id in in_degree:
                adj_list[edge.source_node_id].append(edge.target_node_id)
                in_degree[edge.target_node_id] += 1
                
        # Queue containing nodes with no incoming edges
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        
        execution_order = []
        
        while queue:
            current_id = queue.pop(0)
            execution_order.append(node_map[current_id])
            
            for neighbor_id in adj_list.get(current_id, []):
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)
                    
        if len(execution_order) != len(nodes):
            logger.error("DAG contains cycle! Cannot execute topologically.")
            raise ValueError("Cycle detected in the attack chain DAG.")
            
        return execution_order

dag_engine = DAGEngine()
