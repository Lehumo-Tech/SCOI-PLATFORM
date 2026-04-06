import os
from emergentintegrations.llm.chat import LlmChat, UserMessage
from typing import List, Dict, Optional
import json

class LLMService:
    def __init__(self):
        self.api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment")
    
    async def enhance_entity_matching(self, entity1: Dict, entity2: Dict) -> Dict:
        """Use LLM to determine if two entities are likely the same"""
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"entity_match_{entity1.get('id', 'unknown')}",
            system_message="You are an expert at entity resolution for corruption investigations. Analyze if two entities refer to the same real-world person or organization."
        ).with_model("openai", "gpt-5.2")
        
        prompt = f"""Compare these two entities and determine if they likely refer to the same person/organization:

Entity 1:
Type: {entity1.get('type')}
Name: {entity1.get('raw_name')}
Metadata: {json.dumps(entity1.get('metadata', {}), indent=2)}

Entity 2:
Type: {entity2.get('type')}
Name: {entity2.get('raw_name')}
Metadata: {json.dumps(entity2.get('metadata', {}), indent=2)}

Respond ONLY with a JSON object:
{{
  "match": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""
        
        message = UserMessage(text=prompt)
        response = await chat.send_message(message)
        
        try:
            result = json.loads(response)
            return result
        except:
            return {"match": False, "confidence": 0.0, "reasoning": "Failed to parse LLM response"}
    
    async def infer_relationships(self, entities: List[Dict]) -> List[Dict]:
        """Use LLM to infer potential relationships between entities"""
        if len(entities) < 2:
            return []
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"relationship_inference_{len(entities)}",
            system_message="You are an expert at analyzing corruption networks. Identify potential relationships between entities based on their metadata."
        ).with_model("openai", "gpt-5.2")
        
        entities_str = "\n\n".join([
            f"ID: {e.get('id')}\nType: {e.get('type')}\nName: {e.get('raw_name')}\nMetadata: {json.dumps(e.get('metadata', {}))}"
            for e in entities[:10]
        ])
        
        prompt = f"""Analyze these entities and identify potential relationships (director, beneficial owner, related to, etc.):

{entities_str}

Respond ONLY with a JSON array of relationships:
[
  {{
    "from_id": "entity_id",
    "to_id": "entity_id",
    "type": "relationship_type",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
  }}
]

If no relationships found, return empty array []."""
        
        message = UserMessage(text=prompt)
        response = await chat.send_message(message)
        
        try:
            result = json.loads(response)
            return result if isinstance(result, list) else []
        except:
            return []
    
    async def generate_investigation_report(self, entity: Dict, relationships: List[Dict], red_flags: List[Dict]) -> str:
        """Generate a comprehensive investigation report with citations"""
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"report_{entity.get('id', 'unknown')}",
            system_message="You are an investigative analyst for corruption cases. Generate detailed, factual reports with proper citations."
        ).with_model("openai", "gpt-5.2")
        
        prompt = f"""Generate an investigative report for this entity:

Entity:
Type: {entity.get('type')}
Name: {entity.get('raw_name')}
Metadata: {json.dumps(entity.get('metadata', {}), indent=2)}
Source: {entity.get('source')}

Relationships ({len(relationships)}):
{json.dumps(relationships, indent=2)}

Red Flags ({len(red_flags)}):
{json.dumps(red_flags, indent=2)}

Generate a professional report in Markdown format with:
1. Executive Summary
2. Entity Profile
3. Network Analysis (relationships)
4. Red Flag Analysis
5. Source Citations
6. Compliance Warning (remind this is OSINT analysis, not legal determination)

Use factual language only. Include confidence scores. Cite all sources."""
        
        message = UserMessage(text=prompt)
        response = await chat.send_message(message)
        return response