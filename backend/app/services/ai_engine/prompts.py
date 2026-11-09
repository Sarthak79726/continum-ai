KNOWLEDGE_RECONSTRUCTION_SYSTEM_PROMPT = """You are Continuum AI, an enterprise-grade Knowledge Reconstruction and Continuity Intelligence Engine.
Your mission is to perform deep knowledge handover analysis on authorized project documents.

You must follow these strict epistemic rules:
1. ZERO HALLUCINATION: Extract only factual information present in the source documents. If ownership, dates, status, or decisions are missing, explicitly write "Unknown" or "Not specified in available sources".
2. EVIDENCE GROUNDING: Every claim must be tied to a specific source document and quote snippet.
3. CONFLICT PRESERVATION: If source A states a feature is finished and source B states it is blocked or pending, do NOT guess. Record the conflict explicitly in Unresolved Questions and tag the claim as CONFLICTING.
4. STRUCTURED RECONSTRUCTION: Output strictly valid JSON conforming to the requested schema.
"""

KNOWLEDGE_RECONSTRUCTION_USER_PROMPT = """Analyze the following extracted project document chunks and reconstruct the complete knowledge state of the project.

Context:
{context}

You must return a valid JSON object with EXACTLY the following structure:
{{
  "overview": {{
    "project_purpose": "Clear purpose of the project as stated in documents",
    "main_objectives": ["Objective 1", "Objective 2"],
    "current_development_stage": "Stage (e.g., Alpha, Beta, Integration, Planning)",
    "important_technical_components": ["Component 1", "Component 2"],
    "evidence_snippet": "Direct quote from source establishing project purpose",
    "source_document": "Filename of source"
  }},
  "completed_tasks": [
    {{
      "title": "Task title",
      "description": "What was accomplished",
      "status": "completed",
      "owner": "Name of responsible person or Unknown",
      "completion_evidence": "Direct quote proving completion",
      "source_document": "Filename",
      "page_number": 1,
      "verification_status": "VERIFIED"
    }}
  ],
  "ongoing_tasks": [
    {{
      "title": "Task title",
      "description": "Current progress and remaining work",
      "status": "in_progress",
      "owner": "Name or Unknown",
      "completion_evidence": "Evidence text from document",
      "source_document": "Filename",
      "page_number": 1,
      "verification_status": "NEEDS_REVIEW"
    }}
  ],
  "pending_tasks": [
    {{
      "title": "Task title",
      "description": "What needs to be done",
      "status": "pending",
      "owner": "Name or Unknown",
      "completion_evidence": "Evidence quote",
      "source_document": "Filename",
      "page_number": 1,
      "verification_status": "NEEDS_REVIEW"
    }}
  ],
  "important_decisions": [
    {{
      "title": "Decision title",
      "description": "What was decided",
      "reasoning": "Why this decision was made",
      "date_decided": "Date or Unknown",
      "source_document": "Filename",
      "evidence_snippet": "Quote showing decision"
    }}
  ],
  "risks_and_blockers": [
    {{
      "title": "Risk title",
      "description": "Detailed risk description",
      "severity": "critical | high | medium | low",
      "potential_impact": "Impact on timeline or architecture",
      "suggested_resolution": "Resolution strategy",
      "source_document": "Filename",
      "evidence_snippet": "Quote from document"
    }}
  ],
  "dependencies": [
    {{
      "source_title": "Component or Task A",
      "target_title": "Depends on Component or Task B",
      "dependency_explanation": "Why A needs B",
      "evidence_snippet": "Quote",
      "source_document": "Filename"
    }}
  ],
  "unresolved_questions": [
    {{
      "question": "Clear question",
      "category": "missing_information | contradictory_information | unclear_ownership | unverified_claim",
      "details": "Explanation of ambiguity or contradiction",
      "source_document": "Filename"
    }}
  ],
  "recommended_next_actions": [
    "Prioritized actionable step 1 for incoming member",
    "Prioritized actionable step 2 for incoming member"
  ]
}}
"""

