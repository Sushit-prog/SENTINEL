import logging
from neo4j import GraphDatabase
from backend.config import get_settings

logger = logging.getLogger(__name__)

class GraphDB:
    """
    Neo4j Aura connection manager for FRAUDGraph.
    """

    def __init__(self):
        settings = get_settings()
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
        logger.info("Neo4j connection established.")

    def verify_connectivity(self):
        self.driver.verify_connectivity()
        logger.info("Neo4j connectivity verified.")

    def close(self):
        self.driver.close()

    def run_query(self, query: str, parameters: dict = None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def create_constraints(self):
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:PhoneNumber) REQUIRE p.number IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Device) REQUIRE d.fingerprint IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (v:Victim) REQUIRE v.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (r:FraudRing) REQUIRE r.id IS UNIQUE",
        ]
        for constraint in constraints:
            self.run_query(constraint)
        logger.info("Neo4j constraints created.")

_graph_instance = None

def get_graph_db() -> GraphDB:
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = GraphDB()
    return _graph_instance
