"""Template-based LLM planner for Alpha 0.1.

The LLM acts as a planner — it maps user intent to an allowlisted action
and extracts parameters. It does NOT write code or make engineering decisions.

Privacy mode (NEI_LLM_PRIVACY=on): template-only, no external LLM call.
"""
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PlanStep:
    """One step in an execution plan."""
    action: str
    risk_level: str
    params: dict = field(default_factory=dict)


@dataclass
class Plan:
    """Structured execution plan."""
    task_type: str
    steps: list[PlanStep]
    required_inputs: list[str] = field(default_factory=list)
    notes: Optional[str] = None


# ── Allowlisted templates ────────────────────────────────────────────────────

# Pattern: "create a LxWxH box"
BOX_PATTERN = re.compile(
    r"(?:create|make|build)\s+(?:a\s+|the\s+)?(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)"
    r"(?:\s+box)?\s*(?:in\s+rhino)?",
    re.IGNORECASE,
)

# Default box dimensions for the spike test
DEFAULT_L, DEFAULT_W, DEFAULT_H = 10.0, 3.0, 1.0


def _extract_box_params(user_request: str) -> dict:
    """Extract L/W/H from natural language. Falls back to defaults."""
    m = BOX_PATTERN.search(user_request)
    if m:
        return {"length": float(m.group(1)), "width": float(m.group(2)), "height": float(m.group(3))}
    return {"length": DEFAULT_L, "width": DEFAULT_W, "height": DEFAULT_H}


def _is_box_request(user_request: str) -> bool:
    m = BOX_PATTERN.search(user_request)
    return bool(m) or ("box" in user_request.lower())


HANDOFF_PATTERN = re.compile(
    r"(?:handoff|transfer)\s*(?:a\s+|the\s+)?(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)"
    r"(?:\s+box)?\s*(?:to\s+(\w+))?",
    re.IGNORECASE,
)


def _is_handoff_request(user_request: str) -> bool:
    m = HANDOFF_PATTERN.search(user_request)
    return bool(m) or ("handoff" in user_request.lower() or "transfer" in user_request.lower())


def plan_task(user_request: str, task_type: str = "geometry", hull_design: Optional[dict] = None) -> Plan:
    """Produce a structured plan for a user request.

    Alpha 0.1:
    - Box creation in Rhino 6 → single-step plan with L1 risk
    - Hull design → preview calculation only, no connector claim
    - Phase 8: cross-software handoff → 3-step chain
    - Anything else → fallback step with note
    """
    if task_type == "hull_design" and hull_design:
        from nei.engineering.hull import HullDesignRequest, hull_preview
        try:
            hull = HullDesignRequest.model_validate(hull_design)
            preview = hull_preview(hull)
        except Exception as e:
            return Plan(task_type="hull_design", steps=[], notes=f"Hull validation failed: {e}")
        return Plan(
            task_type="hull_design",
            steps=[
                PlanStep("hull.preview_calculation", "L0", hull_design),
            ],
            notes=f"Preview only: displacement {preview['calculations']['displacement_volume_m3']:.1f} m³, Fn {preview['calculations']['froude_number']:.3f}. No connector claimed.",
        )
    if _is_handoff_request(user_request):
        m = HANDOFF_PATTERN.search(user_request)
        if m:
            l, w, h = float(m.group(1)), float(m.group(2)), float(m.group(3))
            target = m.group(4) or "solidworks2022"
        else:
            l, w, h = DEFAULT_L, DEFAULT_W, DEFAULT_H
            target = "solidworks2022"
        return Plan(
            task_type="handoff",
            steps=[
                PlanStep("rhino.create_box_test", "L1",
                         {"length": l, "width": w, "height": h, "export_format": "STEP"}),
                PlanStep("rhino.export_copy", "L1",
                         {"format": "STEP", "unit": "mm"}),
                PlanStep(f"{target}.import_copy", "L1",
                         {"format": "STEP", "unit": "mm", "verify_bbox": [l, w, h]}),
            ],
            notes=f"Handoff plan: {l}x{w}x{h} box → {target} via STEP",
        )

    if _is_box_request(user_request):
        params = _extract_box_params(user_request)
        return Plan(
            task_type=task_type,
            steps=[
                PlanStep(
                    action="rhino.create_box_test",
                    risk_level="L1",
                    params=params,
                )
            ],
            notes=f"Box plan: {params['length']} x {params['width']} x {params['height']}",
        )

    # Non-box request: no matching template → report required inputs
    return Plan(
        task_type=task_type,
        steps=[],
        required_inputs=["action_type", "parameters"],
        notes="No matching template for Alpha 0.1. LLM extension required.",
    )


def plan_from_llm(user_request: str, task_type: str,
                  llm_fn: Optional[callable] = None) -> Plan:
    """Use LLM to select action when template match fails.

    llm_fn: callable(prompt: str) -> str. Returns raw LLM text.
    Falls back to template if LLM unavailable or returns no action.
    """
    template_plan = plan_task(user_request, task_type)
    if template_plan.steps:
        return template_plan

    if llm_fn is None:
        return template_plan

    prompt = (
        f"You are a planning module for a naval engineering CAD assistant.\n"
        f"User request: {user_request!r}\n"
        f"Allowed actions: rhino.create_box_test, rhino.inspect_objects, rhino.get_document_info\n"
        f"Return ONLY a JSON object: {{\"action\": \"...\", \"params\": {{...}}}}\n"
        f"Do not include other text."
    )
    try:
        raw = llm_fn(prompt)
        import json
        parsed = json.loads(raw)
        action = parsed.get("action", "")
        params = parsed.get("params", {})
        if action in ("rhino.create_box_test", "rhino.inspect_objects", "rhino.get_document_info"):
            return Plan(
                task_type=task_type,
                steps=[PlanStep(action=action, risk_level="L1", params=params)],
                notes="LLM-selected plan",
            )
    except Exception:
        pass
    return template_plan
