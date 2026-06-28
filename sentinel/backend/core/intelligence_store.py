import logging
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.config import get_settings
from backend.core.embeddings import get_embeddings

logger = logging.getLogger(__name__)

class IntelligenceStore:
    """
    Shared ChromaDB intelligence store.
    All three modules write threat patterns here.
    Cross-module intelligence sharing happens through this class.
    """

    def __init__(self):
        settings = get_settings()
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.embeddings = get_embeddings()
        self._init_collections()

    def _init_collections(self):
        self.scam_patterns = self.client.get_or_create_collection(
            name="scam_patterns",
            metadata={"description": "Scam script patterns from SCAMWatch"},
        )
        self.fraud_networks = self.client.get_or_create_collection(
            name="fraud_networks",
            metadata={"description": "Fraud network signatures from FRAUDGraph"},
        )
        self.currency_events = self.client.get_or_create_collection(
            name="currency_events",
            metadata={"description": "Counterfeit detection events from CURRENCYGuard"},
        )
        logger.info("Intelligence store collections initialized.")

    def add_scam_pattern(self, pattern_id: str, text: str, metadata: dict):
        embedding = self.embeddings.embed_query(text)
        self.scam_patterns.add(
            ids=[pattern_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata],
        )

    def query_similar_scams(self, text: str, n_results: int = 5):
        embedding = self.embeddings.embed_query(text)
        return self.scam_patterns.query(
            query_embeddings=[embedding],
            n_results=n_results,
        )

    def add_fraud_network(self, network_id: str, description: str, metadata: dict):
        embedding = self.embeddings.embed_query(description)
        self.fraud_networks.add(
            ids=[network_id],
            embeddings=[embedding],
            documents=[description],
            metadatas=[metadata],
        )

    def add_currency_event(self, event_id: str, description: str, metadata: dict):
        embedding = self.embeddings.embed_query(description)
        self.currency_events.add(
            ids=[event_id],
            embeddings=[embedding],
            documents=[description],
            metadatas=[metadata],
        )

_store_instance = None

def get_intelligence_store() -> IntelligenceStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = IntelligenceStore()
    return _store_instance
