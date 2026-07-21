import uuid
import json
import logging
from typing import List, Dict, Tuple
from backend.models.fraud_models import Entity, Relationship, EntityType
from backend.core.llm import get_llm
from backend.core.graph_db import get_graph_db

logger = logging.getLogger(__name__)

# Pronouns and common short words that should NOT be valid victim names
INVALID_VICTIM_NAMES = {
    "i", "me", "my", "mine", "myself",
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "they", "them", "their", "theirs", "themselves",
    "we", "us", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself",
    "it", "its", "itself",
    "the", "a", "an", "this", "that", "these", "those",
    "someone", "somebody", "anyone", "anybody", "everyone", "nobody",
}

ENTITY_EXTRACTION_PROMPT = """You are a fraud intelligence analyst. Extract all entities from this victim statement.

Return ONLY a valid JSON object with this exact structure:
{{
  "entities": [
    {{"type": "PHONE|ACCOUNT|DEVICE|VICTIM|LOCATION", "value": "the extracted value"}}
  ],
  "relationships": [
    {{"from_value": "value1", "to_value": "value2", "type": "CALLED|TRANSFERRED_TO|USED_BY|CONTACTED|BELONGS_TO", "description": "brief reason"}}
  ]
}}

Entity type rules:
- PHONE: any phone number mentioned
- ACCOUNT: bank account numbers, UPI IDs, wallet IDs
- DEVICE: device IDs, IMEI, MAC addresses, any device identifier
- VICTIM: victim names ONLY if explicitly stated (e.g. "my name is Rajesh", "the victim Priya said"). NEVER extract pronouns (I, me, my, he, she, they, him, her) as victim names. If no real name is given, DO NOT include a VICTIM entity at all.
- LOCATION: cities, states, IP addresses, regions

Relationship type rules:
- CALLED: phone called another phone or victim
- TRANSFERRED_TO: money transferred between accounts
- USED_BY: device used by a phone/account
- CONTACTED: any entity contacted a victim
- BELONGS_TO: phone/device belongs to an account or person

Statement: {statement}

Return only the JSON object. No preamble, no explanation, no markdown fences."""


class GraphBuilder:
    def __init__(self):
        self.llm = get_llm()
        self.graph_db = get_graph_db()

    def parse_structured_inputs(
        self,
        phones: List[str],
        accounts: List[str],
        devices: List[str]
    ) -> List[Entity]:
        """Convert raw structured inputs to Entity objects."""
        entities = []

        for phone in phones:
            phone = phone.strip()
            if phone:
                entities.append(Entity(
                    id=f"PHONE_{phone.replace(' ', '').replace('+', '')}",
                    type=EntityType.PHONE,
                    value=phone,
                    metadata={"source": "analyst_input"}
                ))

        for account in accounts:
            account = account.strip()
            if account:
                entities.append(Entity(
                    id=f"ACCOUNT_{account.replace(' ', '')}",
                    type=EntityType.ACCOUNT,
                    value=account,
                    metadata={"source": "analyst_input"}
                ))

        for device in devices:
            device = device.strip()
            if device:
                entities.append(Entity(
                    id=f"DEVICE_{device.replace(' ', '')}",
                    type=EntityType.DEVICE,
                    value=device,
                    metadata={"source": "analyst_input"}
                ))

        return entities

    def extract_from_statement(self, victim_statement: str) -> Tuple[List[Entity], List[Relationship]]:
        """Use Groq LLM to extract entities and relationships from free text."""
        if not victim_statement or len(victim_statement.strip()) < 10:
            return [], []

        try:
            prompt = ENTITY_EXTRACTION_PROMPT.format(statement=victim_statement)
            response = self.llm.invoke(prompt)
            content = response.content.strip()

            # Clean markdown fences if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            data = json.loads(content)

            entities = []
            entity_map = {}  # value -> id for relationship building
            victim_count = 0  # Track generic victims

            for e in data.get("entities", []):
                etype = e.get("type", "PHONE")
                value = str(e.get("value", "")).strip()
                if not value:
                    continue

                # Filter out pronouns as victim names
                if etype == "VICTIM":
                    value_lower = value.lower().strip()
                    # Reject pronouns and common short words
                    if value_lower in INVALID_VICTIM_NAMES or len(value) <= 1:
                        # Replace with generic victim identifier
                        victim_count += 1
                        value = f"VICTIM_{victim_count}"
                    # Reject if it's just a pronoun phrase like "I" or "me"
                    elif value_lower.startswith(("i ", "me ", "my ", "he ", "she ", "they ")):
                        victim_count += 1
                        value = f"VICTIM_{victim_count}"

                entity_id = f"{etype}_{value.replace(' ', '').replace('+', '')}"
                entity = Entity(
                    id=entity_id,
                    type=EntityType(etype),
                    value=value,
                    metadata={"source": "llm_extracted"}
                )
                entities.append(entity)
                entity_map[value] = entity_id

            relationships = []
            for r in data.get("relationships", []):
                from_val = str(r.get("from_value", ""))
                to_val = str(r.get("to_value", ""))
                rel_type = r.get("type", "CONTACTED")
                if from_val in entity_map and to_val in entity_map:
                    relationships.append(Relationship(
                        from_id=entity_map[from_val],
                        to_id=entity_map[to_val],
                        rel_type=rel_type,
                        weight=1.0
                    ))

            return entities, relationships

        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return [], []

    def infer_relationships(self, entities: List[Entity]) -> List[Relationship]:
        """
        Infer implicit relationships from co-occurrence in structured input.
        If multiple phones are given together, they likely CALLED each other.
        If phones and accounts are given together, phone BELONGS_TO account.
        """
        relationships = []
        phones = [e for e in entities if e.type == EntityType.PHONE]
        accounts = [e for e in entities if e.type == EntityType.ACCOUNT]
        devices = [e for e in entities if e.type == EntityType.DEVICE]

        # Phones in same submission: assume they called each other (ring)
        for i in range(len(phones)):
            for j in range(i + 1, len(phones)):
                relationships.append(Relationship(
                    from_id=phones[i].id,
                    to_id=phones[j].id,
                    rel_type="CALLED",
                    weight=0.8
                ))

        # Accounts in same submission: assume money transfer chain
        for i in range(len(accounts) - 1):
            relationships.append(Relationship(
                from_id=accounts[i].id,
                to_id=accounts[i + 1].id,
                rel_type="TRANSFERRED_TO",
                weight=0.9
            ))

        # Each device linked to first phone (if both present)
        if phones and devices:
            for device in devices:
                relationships.append(Relationship(
                    from_id=device.id,
                    to_id=phones[0].id,
                    rel_type="USED_BY",
                    weight=0.7
                ))

        return relationships

    def write_to_neo4j(self, entities: List[Entity], relationships: List[Relationship]):
        """Write all entities and relationships to Neo4j."""
        for entity in entities:
            self.graph_db.merge_entity(
                entity_id=entity.id,
                entity_type=entity.type.value,
                value=entity.value,
                metadata=entity.metadata
            )

        for rel in relationships:
            self.graph_db.merge_relationship(
                from_id=rel.from_id,
                to_id=rel.to_id,
                rel_type=rel.rel_type,
                weight=rel.weight
            )

    def build(
        self,
        phones: List[str],
        accounts: List[str],
        devices: List[str],
        victim_statement: str
    ) -> Tuple[List[Entity], List[Relationship]]:
        """
        Full entity resolution pipeline:
        1. Parse structured inputs
        2. Extract from victim statement (LLM)
        3. Merge deduplicated entities
        4. Infer implicit relationships
        5. Write to Neo4j
        Returns: (entities, relationships)
        """
        # Step 1: structured
        structured_entities = self.parse_structured_inputs(phones, accounts, devices)

        # Step 2: LLM extraction
        llm_entities, llm_relationships = self.extract_from_statement(victim_statement)

        # Step 3: Merge and deduplicate by id
        all_entities_map = {e.id: e for e in structured_entities}
        for e in llm_entities:
            if e.id not in all_entities_map:
                all_entities_map[e.id] = e
        all_entities = list(all_entities_map.values())

        # Step 4: Infer implicit relationships
        inferred_rels = self.infer_relationships(structured_entities)
        all_relationships_map = {(r.from_id, r.to_id, r.rel_type): r for r in inferred_rels}
        for r in llm_relationships:
            key = (r.from_id, r.to_id, r.rel_type)
            if key not in all_relationships_map:
                all_relationships_map[key] = r
        all_relationships = list(all_relationships_map.values())

        # Step 5: Write to Neo4j
        self.write_to_neo4j(all_entities, all_relationships)

        return all_entities, all_relationships
