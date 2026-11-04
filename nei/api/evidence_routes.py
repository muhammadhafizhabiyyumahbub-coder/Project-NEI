"""Phase 4 evidence + formula API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from nei.evidence import (
    ingest_source,
    list_sources,
    get_source,
    verify_source_checksum,
    set_source_status,
    search,
    register_formula,
    get_formula,
    list_formulas,
    advance_formula,
    get_chunk,
)
from nei.evidence.citation_builder import build_citation


router = APIRouter()


# ── Request models ────────────────────────────────────────────────────────────
class IngestSourceRequest(BaseModel):
    title: str
    source_type: str
    authority_level: str
    local_file_path: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    edition: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    official_url: Optional[str] = None


class SourceStatusRequest(BaseModel):
    status: str
    reason: str = ""


class SearchRequest(BaseModel):
    query: str
    source_id: Optional[str] = None
    limit: int = 20


class FormulaRequest(BaseModel):
    name: str
    domain: str
    equation_text: str
    implementation_ref: Optional[str] = None
    variables: Optional[list[dict]] = None
    assumptions: Optional[list[str]] = None
    applicability: Optional[list[str]] = None
    source_refs: Optional[list[str]] = None
    source_locations: Optional[list[dict]] = None


class FormulaAdvanceRequest(BaseModel):
    to_status: str
    reviewed_by: str = "user"
    reason: str = ""


class CitationRequest(BaseModel):
    chunk_id: str
    source_id: str


# ── Evidence endpoints ────────────────────────────────────────────────────────
@router.post("/evidence/sources")
async def ingest_endpoint(body: IngestSourceRequest):
    try:
        return await ingest_source(
            body.title, body.source_type, body.authority_level,
            body.local_file_path,
            author=body.author, publisher=body.publisher, edition=body.edition,
            year=body.year, doi=body.doi, official_url=body.official_url,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/evidence/sources")
async def list_sources_endpoint():
    return await list_sources()


@router.get("/evidence/sources/{source_id}")
async def get_source_endpoint(source_id: str):
    src = await get_source(source_id)
    if not src:
        raise HTTPException(status_code=404, detail="Source not found")
    return src


@router.post("/evidence/sources/{source_id}/checksum")
async def checksum_endpoint(source_id: str):
    try:
        return await verify_source_checksum(source_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/evidence/sources/{source_id}/status")
async def source_status_endpoint(source_id: str, body: SourceStatusRequest):
    try:
        return await set_source_status(source_id, body.status, body.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/evidence/search")
async def search_endpoint(body: SearchRequest):
    return await search(body.query, body.source_id, body.limit)


# New: citation endpoint
class CitationRequest(BaseModel):
    chunk_id: str
    source_id: str


class CitationResponse(BaseModel):
    citation: str


@router.post("/evidence/citation")
async def citation_endpoint(body: CitationRequest):
    source = await get_source(body.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    chunk = await get_chunk(body.chunk_id)
    if not chunk or chunk["source_id"] != body.source_id:
        raise HTTPException(status_code=404, detail="Chunk not found for source")
    return {"citation": build_citation(chunk, source)}


# ── Formula endpoints ────────────────────────────────────────────────────────
class FormulaRequest(BaseModel):
    name: str
    domain: str
    equation_text: str
    implementation_ref: Optional[str] = None
    variables: Optional[list[dict]] = None
    assumptions: Optional[list[str]] = None
    applicability: Optional[list[str]] = None
    source_refs: Optional[list[str]] = None
    source_locations: Optional[list[dict]] = None


class FormulaAdvanceRequest(BaseModel):
    to_status: str
    reviewed_by: str = "user"
    reason: str = ""


@router.post("/formulas")
async def register_formula_endpoint(body: FormulaRequest):
    return await register_formula(
        body.name, body.domain, body.equation_text,
        implementation_ref=body.implementation_ref,
        variables=body.variables, assumptions=body.assumptions,
        applicability=body.applicability,
        source_refs=body.source_refs, source_locations=body.source_locations,
    )


@router.get("/formulas")
async def list_formulas_endpoint(domain: Optional[str] = None, status: Optional[str] = None):
    return await list_formulas(domain, status)


@router.get("/formulas/{formula_id}")
async def get_formula_endpoint(formula_id: str):
    f = await get_formula(formula_id)
    if not f:
        raise HTTPException(status_code=404, detail="Formula not found")
    return f


@router.post("/formulas/{formula_id}/advance")
async def advance_formula_endpoint(formula_id: str, body: FormulaAdvanceRequest):
    try:
        return await advance_formula(formula_id, body.to_status,
                                     body.reviewed_by, body.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))