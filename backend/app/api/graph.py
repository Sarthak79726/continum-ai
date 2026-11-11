import math
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user, check_project_access
from app.models.all_models import (
    Project, Task, Decision, Risk, Dependency, Document, User, ExtractedKnowledge,
    EmployeeProfile, APIEndpointRecord, BugDebtItem, CommitRecord
)
from app.schemas.all_schemas import KnowledgeGraphResponse, GraphNode, GraphEdge, GraphNodeData

router = APIRouter(tags=["Knowledge Graph"])

@router.get("/projects/{project_id}/graph", response_model=KnowledgeGraphResponse)
def get_project_knowledge_graph(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = check_project_access(project_id, current_user, db)

    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []
    node_id_set = set()

    # 1. Project Center Node
    root_id = f"proj_{project.id}"
    nodes.append(GraphNode(
        id=root_id,
        type="project",
        data=GraphNodeData(
            label=project.name,
            type="project",
            status=project.status,
            details=project.description or "Root Project"
        ),
        position={"x": 500, "y": 300}
    ))
    node_id_set.add(root_id)

    # 2. Key Employee / Person Nodes
    tasks = db.query(Task).filter(Task.project_id == project.id).all()
    db_employees = db.query(EmployeeProfile).filter(EmployeeProfile.project_id == project.id).all()
    person_nodes = []
    
    if db_employees:
        for i, emp in enumerate(db_employees):
            p_id = f"emp_{emp.id}"
            x = 150 + i * 220
            y = 100
            nodes.append(GraphNode(
                id=p_id,
                type="person",
                data=GraphNodeData(
                    label=emp.name,
                    type="person",
                    status=emp.handover_status,
                    details=f"{emp.role_title} ({emp.department})"
                ),
                position={"x": x, "y": y}
            ))
            node_id_set.add(p_id)
            edges.append(GraphEdge(
                id=f"e_{p_id}_{root_id}",
                source=p_id,
                target=root_id,
                label=f"Role: {emp.role_title}"
            ))
            person_nodes.append((emp.name, p_id))
    else:
        persons = set()
        for t in tasks:
            if t.owner and t.owner not in ["Unknown", "Unassigned", "Incoming Engineer"]:
                persons.add(t.owner)

        if not persons and project.owner:
            persons.add(project.owner.name)

        for i, p_name in enumerate(list(persons)):
            p_id = f"person_{i}"
            x = 200 + i * 220
            y = 120
            nodes.append(GraphNode(
                id=p_id,
                type="person",
                data=GraphNodeData(
                    label=p_name,
                    type="person",
                    details=f"Team Member / Contributor on {project.name}"
                ),
                position={"x": x, "y": y}
            ))
            node_id_set.add(p_id)
            edges.append(GraphEdge(
                id=f"e_{p_id}_{root_id}",
                source=p_id,
                target=root_id,
                label="Contributes to"
            ))
            person_nodes.append((p_name, p_id))

    # 3. Technical Component Nodes from Overview
    overview_entry = db.query(ExtractedKnowledge).filter(
        ExtractedKnowledge.project_id == project.id,
        ExtractedKnowledge.category == "overview"
    ).first()
    components = []
    if overview_entry and isinstance(overview_entry.structured_content, dict):
        components = overview_entry.structured_content.get("important_technical_components", [])

    for i, comp in enumerate(components[:4]):
        c_id = f"comp_{i}"
        angle = (i * (2 * math.pi / 4))
        x = 500 + int(320 * math.cos(angle))
        y = 300 + int(180 * math.sin(angle))
        nodes.append(GraphNode(
            id=c_id,
            type="component",
            data=GraphNodeData(
                label=comp,
                type="component",
                details="Core Architecture Subsystem"
            ),
            position={"x": x, "y": y}
        ))
        node_id_set.add(c_id)
        edges.append(GraphEdge(
            id=f"e_{root_id}_{c_id}",
            source=root_id,
            target=c_id,
            label="Component"
        ))

    # 4. Task Nodes & Connect to Owners and Components
    for i, t in enumerate(tasks[:8]):
        t_id = f"task_{t.id}"
        x = 100 + (i % 4) * 260
        y = 480 + (i // 4) * 160
        nodes.append(GraphNode(
            id=t_id,
            type="task",
            data=GraphNodeData(
                label=t.title,
                type="task",
                status=t.status,
                priority=t.priority,
                details=t.description,
                evidence=t.source_reference
            ),
            position={"x": x, "y": y}
        ))
        node_id_set.add(t_id)

        # Connect task to person if owner matches
        matched_person = False
        for p_name, p_node_id in person_nodes:
            if t.owner and p_name.lower().split()[0] in t.owner.lower():
                edges.append(GraphEdge(
                    id=f"e_{p_node_id}_{t_id}",
                    source=p_node_id,
                    target=t_id,
                    label="Assigned to"
                ))
                matched_person = True
                break
        if not matched_person:
            edges.append(GraphEdge(
                id=f"e_{root_id}_{t_id}",
                source=root_id,
                target=t_id,
                label="Task"
            ))

    # 5. API Endpoint Nodes (from APIEndpointRecord)
    db_apis = db.query(APIEndpointRecord).filter(APIEndpointRecord.project_id == project.id).all()
    for i, api in enumerate(db_apis[:6]):
        api_id = f"api_{api.id}"
        x = 350 + (i % 3) * 220
        y = 650 + (i // 3) * 120
        nodes.append(GraphNode(
            id=api_id,
            type="component",
            data=GraphNodeData(
                label=f"{api.method} {api.endpoint_path}",
                type="component",
                status=api.implementation_status,
                details=f"Module: {api.backend_module} | Auth: {api.permissions_required}",
                evidence=api.source_reference
            ),
            position={"x": x, "y": y}
        ))
        node_id_set.add(api_id)
        if api.employee_id:
            edges.append(GraphEdge(
                id=f"e_emp_{api.employee_id}_{api_id}",
                source=f"emp_{api.employee_id}",
                target=api_id,
                label=f"Implemented ({api.implementation_status})",
                style={"stroke": "#10b981" if api.implementation_status == "COMPLETED" else "#f59e0b"}
            ))

    # 6. Bug Debt Nodes (from BugDebtItem)
    db_bugs = db.query(BugDebtItem).filter(BugDebtItem.project_id == project.id).all()
    for i, b in enumerate(db_bugs[:4]):
        b_id = f"bug_{b.id}"
        x = 750 + (i % 2) * 200
        y = 650 + (i // 2) * 120
        nodes.append(GraphNode(
            id=b_id,
            type="risk",
            data=GraphNodeData(
                label=f"[{b.issue_code}] {b.title[:24]}...",
                type="risk",
                severity=b.severity,
                status=b.classification,
                details=b.description,
                evidence=b.evidence_snippet
            ),
            position={"x": x, "y": y}
        ))
        node_id_set.add(b_id)
        if b.employee_id:
            edges.append(GraphEdge(
                id=f"e_emp_{b.employee_id}_{b_id}",
                source=f"emp_{b.employee_id}",
                target=b_id,
                label=f"Debt: {b.classification}",
                style={"stroke": "#ef4444", "strokeDasharray": "4 4"}
            ))

    # 7. Risk Nodes
    risks = db.query(Risk).filter(Risk.project_id == project.id).all()
    for i, r in enumerate(risks[:3]):
        r_id = f"risk_{r.id}"
        x = 880
        y = 120 + i * 150
        nodes.append(GraphNode(
            id=r_id,
            type="risk",
            data=GraphNodeData(
                label=r.title,
                type="risk",
                severity=r.severity,
                details=r.description,
                evidence=r.suggested_resolution
            ),
            position={"x": x, "y": y}
        ))
        node_id_set.add(r_id)
        edges.append(GraphEdge(
            id=f"e_{root_id}_{r_id}",
            source=root_id,
            target=r_id,
            label=f"Risk ({r.severity.upper()})",
            style={"stroke": "#ef4444", "strokeDasharray": "5 5"}
        ))

    # 8. Decision Nodes
    decisions = db.query(Decision).filter(Decision.project_id == project.id).all()
    for i, d in enumerate(decisions[:3]):
        d_id = f"dec_{d.id}"
        x = 80
        y = 280 + i * 150
        nodes.append(GraphNode(
            id=d_id,
            type="decision",
            data=GraphNodeData(
                label=d.title,
                type="decision",
                details=d.description,
                evidence=d.reasoning
            ),
            position={"x": x, "y": y}
        ))
        node_id_set.add(d_id)
        edges.append(GraphEdge(
            id=f"e_{d_id}_{root_id}",
            source=d_id,
            target=root_id,
            label="Architecture Decision"
        ))

    # 7. Explicit Dependencies
    deps = db.query(Dependency).filter(Dependency.project_id == project.id).all()
    for i, dep in enumerate(deps):
        # Find matching task or component nodes
        src_id = None
        tgt_id = None
        for n in nodes:
            if dep.source_title.lower() in n.data.label.lower() or n.data.label.lower() in dep.source_title.lower():
                src_id = n.id
            if dep.target_title.lower() in n.data.label.lower() or n.data.label.lower() in dep.target_title.lower():
                tgt_id = n.id

        if src_id and tgt_id and src_id != tgt_id:
            edges.append(GraphEdge(
                id=f"e_dep_{i}_{src_id}_{tgt_id}",
                source=src_id,
                target=tgt_id,
                label="Depends on",
                animated=True,
                style={"stroke": "#06b6d4", "strokeWidth": 2}
            ))

    return KnowledgeGraphResponse(nodes=nodes, edges=edges)

