import networkx as nx
from typing import List
from app.models.schemas import TransactionBase


class GraphAgent:
    def __init__(self):
        # MultiDiGraph preserves every transaction edge — DiGraph would silently
        # overwrite duplicate sender→receiver pairs, losing transaction history.
        self.graph = nx.MultiDiGraph()

    def process_transactions(self, transactions: List[TransactionBase]) -> nx.MultiDiGraph:
        """
        Ingests raw transactions and constructs the live knowledge graph.
        Each transaction becomes a directed, labelled edge.  Node attributes
        track aggregate stats needed by dormant-activation and pass-through
        detectors.
        """
        for txn in transactions:
            for node_id in (txn.sender_id, txn.receiver_id):
                if not self.graph.has_node(node_id):
                    self.graph.add_node(
                        node_id,
                        type="Account",
                        is_suspect=False,
                        total_sent=0.0,
                        total_received=0.0,
                        channels=set(),
                        first_seen=txn.timestamp,
                        last_seen=txn.timestamp,
                    )

            # Maintain per-node aggregates for scorer signals
            n_sender = self.graph.nodes[txn.sender_id]
            n_receiver = self.graph.nodes[txn.receiver_id]

            n_sender["total_sent"] = n_sender.get("total_sent", 0.0) + txn.amount
            n_sender["channels"] = n_sender.get("channels", set()) | {txn.channel}
            n_sender["last_seen"] = max(n_sender.get("last_seen", txn.timestamp), txn.timestamp)

            n_receiver["total_received"] = n_receiver.get("total_received", 0.0) + txn.amount
            n_receiver["channels"] = n_receiver.get("channels", set()) | {txn.channel}
            n_receiver["last_seen"] = max(n_receiver.get("last_seen", txn.timestamp), txn.timestamp)

            self.graph.add_edge(
                txn.sender_id,
                txn.receiver_id,
                txn_id=txn.txn_id,
                amount=txn.amount,
                timestamp=txn.timestamp,
                channel=txn.channel,
            )

        return self.graph

    def get_graph(self) -> nx.MultiDiGraph:
        return self.graph
