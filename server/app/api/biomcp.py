"""
HealthFinder BioMCP Integration API Module

This module implements API endpoints for integrating with BioMCP, providing access to
clinical trials, biomedical research literature, and genomic variants data.
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
import httpx
from loguru import logger
from enum import Enum
import json
import asyncio

# Import BioMCP SDK components
try:
    from biomcp.trials.search import TrialQuery, search_trials
    from biomcp.trials.getter import get_trial, Module
    from biomcp.articles.search import search_articles, PubmedRequest
    from biomcp.articles.fetch import fetch_articles
    from biomcp.variants.search import VariantQuery, search_variants
    from biomcp.variants.getter import get_variant
    HAS_BIOMCP = True
except ImportError:
    logger.warning("BioMCP SDK not installed. Using mock implementations.")
    HAS_BIOMCP = False

from app.core.config import settings

# Router definition
router = APIRouter()

# Enums for standardization
class OutputFormat(str, Enum):
    """Output format options for BioMCP responses."""
    JSON = "json"
    MARKDOWN = "markdown"

class TrialPhase(str, Enum):
    """Clinical trial phase options."""
    EARLY_PHASE1 = "EARLY_PHASE1"
    PHASE1 = "PHASE1"
    PHASE2 = "PHASE2"
    PHASE3 = "PHASE3"
    PHASE4 = "PHASE4"
    NOT_APPLICABLE = "NOT_APPLICABLE"

class TrialStatus(str, Enum):
    """Clinical trial status options."""
    RECRUITING = "RECRUITING"
    ACTIVE_NOT_RECRUITING = "ACTIVE_NOT_RECRUITING"
    NOT_YET_RECRUITING = "NOT_YET_RECRUITING"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    WITHDRAWN = "WITHDRAWN"
    SUSPENDED = "SUSPENDED"
    UNKNOWN = "UNKNOWN"

class VariantSignificance(str, Enum):
    """Variant clinical significance options."""
    PATHOGENIC = "pathogenic"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    UNCERTAIN_SIGNIFICANCE = "uncertain_significance"
    LIKELY_BENIGN = "likely_benign"
    BENIGN = "benign"

# Pydantic models for request and response
class TrialSearchRequest(BaseModel):
    """Request model for clinical trial search."""
    condition: Optional[str] = Field(None, description="Medical condition or disease")
    intervention: Optional[str] = Field(None, description="Treatment or intervention")
    target: Optional[str] = Field(None, description="Molecular target")
    gene: Optional[str] = Field(None, description="Gene symbol")
    sponsor: Optional[str] = Field(None, description="Trial sponsor organization")
    location: Optional[str] = Field(None, description="Geographic location")
    distance: Optional[int] = Field(None, description="Distance from location in miles", ge=1, le=500)
    phase: Optional[List[TrialPhase]] = Field(None, description="Trial phase(s)")
    status: Optional[List[TrialStatus]] = Field(None, description="Trial status(es)")
    age: Optional[int] = Field(None, description="Patient age in years", ge=0, le=120)
    gender: Optional[str] = Field(None, description="Patient gender")
    size: int = Field(10, description="Number of results to return", ge=1, le=100)
    page: int = Field(1, description="Page number for pagination", ge=1)
    format: OutputFormat = Field(OutputFormat.JSON, description="Output format")

class ArticleSearchRequest(BaseModel):
    """Request model for biomedical article search."""
    query: Optional[str] = Field(None, description="Free text search query")
    disease: Optional[str] = Field(None, description="Disease or condition")
    gene: Optional[str] = Field(None, description="Gene symbol")
    protein: Optional[str] = Field(None, description="Protein name")
    chemical: Optional[str] = Field(None, description="Chemical or drug name")
    species: Optional[str] = Field(None, description="Species name")
    date_range: Optional[str] = Field(None, description="Date range (e.g., '2020-01-01:2022-12-31')")
    journal: Optional[str] = Field(None, description="Journal name")
    author: Optional[str] = Field(None, description="Author name")
    size: int = Field(10, description="Number of results to return", ge=1, le=100)
    page: int = Field(1, description="Page number for pagination", ge=1)
    format: OutputFormat = Field(OutputFormat.JSON, description="Output format")

class VariantSearchRequest(BaseModel):
    """Request model for genomic variant search."""
    gene: Optional[str] = Field(None, description="Gene symbol")
    variant: Optional[str] = Field(None, description="Variant identifier")
    chromosome: Optional[str] = Field(None, description="Chromosome")
    position: Optional[int] = Field(None, description="Genomic position")
    reference: Optional[str] = Field(None, description="Reference allele")
    alternate: Optional[str] = Field(None, description="Alternate allele")
    significance: Optional[VariantSignificance] = Field(None, description="Clinical significance")
    condition: Optional[str] = Field(None, description="Associated condition or disease")
    size: int = Field(10, description="Number of results to return", ge=1, le=100)
    format: OutputFormat = Field(OutputFormat.JSON, description="Output format")

class BioMCPResponse(BaseModel):
    """Generic response model for BioMCP data."""
    data: Any
    format: OutputFormat
    query_params: Dict[str, Any]

# API endpoints for clinical trials
@router.post("/trials/search", response_model=BioMCPResponse)
async def search_clinical_trials(request: TrialSearchRequest):
    """
    Search for clinical trials based on various criteria.
    
    This endpoint uses BioMCP to search ClinicalTrials.gov for trials matching the specified criteria.
    Results can be returned in either JSON or Markdown format.
    
    Args:
        request: Search parameters for clinical trials
        
    Returns:
        BioMCPResponse: Clinical trials matching the search criteria
    """
    logger.info(
        "Clinical trials search request", 
        extra={
            "condition": request.condition,
            "intervention": request.intervention,
            "phase": request.phase,
            "status": request.status,
            "size": request.size,
            "page": request.page
        }
    )
    
    try:
        if not HAS_BIOMCP:
            # Mock implementation if BioMCP SDK is not available
            mock_data = {"message": "BioMCP SDK not installed. This is mock data."}
            return BioMCPResponse(
                data=mock_data,
                format=request.format,
                query_params=request.dict(exclude_none=True)
            )
        
        # Convert request parameters to TrialQuery format
        query_params = {}

        # Map condition to conditions list
        if request.condition:
            query_params["conditions"] = [request.condition]

        # Map intervention 
        if request.intervention:
            query_params["interventions"] = [request.intervention]

        # Map other parameters to correct field names
        if request.gene:
            # Add gene to general terms
            if "terms" not in query_params:
                query_params["terms"] = []
            query_params["terms"].append(request.gene)

        if request.target:
            # Add target to general terms  
            if "terms" not in query_params:
                query_params["terms"] = []
            query_params["terms"].append(request.target)

        # Handle sponsor, location manually or as terms since TrialQuery may not have direct fields
        if request.sponsor:
            if "terms" not in query_params:
                query_params["terms"] = []
            query_params["terms"].append(request.sponsor)

        # Phase - take first value if multiple provided (TrialQuery expects single enum)
        if request.phase:
            query_params["phase"] = request.phase[0].value  # Take first phase

        # Status - map to recruiting_status (single enum, convert our status enum)
        if request.status:
            # Map first status to recruiting_status
            # This is a simplified mapping - you may need to adjust based on exact enum mapping
            query_params["recruiting_status"] = request.status[0].value

        # Use page_size instead of size for pagination
        query_params["page_size"] = request.size
        
        # Create TrialQuery and execute search
        query = TrialQuery(**query_params)
        output_json = request.format == OutputFormat.JSON
        result = await search_trials(query, output_json=output_json)
        
        # Parse result based on format
        if output_json:
            data = json.loads(result)
        else:
            data = result  # Return markdown as-is
        
        return BioMCPResponse(
            data=data,
            format=request.format,
            query_params=request.dict(exclude_none=True)
        )
    
    except Exception as e:
        logger.error(f"Error searching clinical trials: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching clinical trials: {str(e)}"
        )

@router.get("/trials/{nct_id}", response_model=BioMCPResponse)
async def get_clinical_trial(
    nct_id: str,
    format: OutputFormat = OutputFormat.JSON
):
    """
    Get detailed information about a specific clinical trial.
    
    Args:
        nct_id: ClinicalTrials.gov identifier (NCT number)
        format: Output format (JSON or Markdown)
        
    Returns:
        BioMCPResponse: Detailed information about the clinical trial
    """
    logger.info(f"Clinical trial details request for NCT ID: {nct_id}")
    
    try:
        if not HAS_BIOMCP:
            # Mock implementation if BioMCP SDK is not available
            mock_data = {
                "message": "BioMCP SDK not installed. This is mock data.",
                "nct_id": nct_id
            }
            return BioMCPResponse(
                data=mock_data,
                format=format,
                query_params={"nct_id": nct_id, "format": format}
            )
        
        # Get trial details
        output_json = format == OutputFormat.JSON
        # The BioMCP getter requires a Module argument (use PROTOCOL by default)
        result = await get_trial(
            nct_id,
            module=Module.PROTOCOL,
            output_json=output_json,
        )
        
        # Parse result based on format
        if output_json:
            data = json.loads(result)
        else:
            data = result  # Return markdown as-is
        
        return BioMCPResponse(
            data=data,
            format=format,
            query_params={"nct_id": nct_id, "format": format}
        )
    
    except Exception as e:
        logger.error(f"Error retrieving clinical trial details: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving clinical trial details: {str(e)}"
        )

# API endpoints for biomedical articles
@router.post("/articles/search", response_model=BioMCPResponse)
async def search_biomedical_articles(request: ArticleSearchRequest):
    """
    Search for biomedical research articles based on various criteria.
    
    This endpoint uses BioMCP to search PubMed for articles matching the specified criteria.
    Results can be returned in either JSON or Markdown format.
    
    Args:
        request: Search parameters for biomedical articles
        
    Returns:
        BioMCPResponse: Articles matching the search criteria
    """
    logger.info(
        "Biomedical articles search request", 
        extra={
            "query": request.query,
            "disease": request.disease,
            "gene": request.gene,
            "size": request.size,
            "page": request.page
        }
    )
    
    try:
        if not HAS_BIOMCP:
            # Mock implementation if BioMCP SDK is not available
            mock_data = {"message": "BioMCP SDK not installed. This is mock data."}
            return BioMCPResponse(
                data=mock_data,
                format=request.format,
                query_params=request.dict(exclude_none=True)
            )
        
        # ------------------------------------------------------------------ #
        # Map our API parameters to the BioMCP `PubmedRequest` model fields. #
        # The current SDK expects LISTS for these fields:                    #
        #   diseases • genes • chemicals • keywords • variants              #
        # ------------------------------------------------------------------ #
        diseases: List[str] = []
        genes: List[str] = []
        chemicals: List[str] = []
        keywords: List[str] = []
        variants: List[str] = []

        if request.disease:
            diseases.append(request.disease)
        if request.gene:
            genes.append(request.gene)
        if request.chemical:
            chemicals.append(request.chemical)

        # Treat free-text query, protein, and species as generic keywords
        for kw in (request.query, request.protein, request.species):
            if kw:
                keywords.append(kw)

        # Create PubmedRequest with properly mapped parameters
        query = PubmedRequest(
            diseases=diseases,
            genes=genes,
            chemicals=chemicals,
            keywords=keywords,
            variants=variants,
        )

        output_json = request.format == OutputFormat.JSON
        result = await search_articles(query, output_json=output_json)
        
        # Parse result based on format
        if output_json:
            data = json.loads(result)
        else:
            data = result  # Return markdown as-is
        
        return BioMCPResponse(
            data=data,
            format=request.format,
            query_params=request.dict(exclude_none=True)
        )
    
    except Exception as e:
        logger.error(f"Error searching biomedical articles: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching biomedical articles: {str(e)}"
        )

@router.get("/articles/{pmid}", response_model=BioMCPResponse)
async def get_article_details(
    pmid: str,
    format: OutputFormat = OutputFormat.JSON
):
    """
    Get detailed information about a specific biomedical article.
    
    Args:
        pmid: PubMed ID
        format: Output format (JSON or Markdown)
        
    Returns:
        BioMCPResponse: Detailed information about the article
    """
    logger.info(f"Article details request for PMID: {pmid}")
    
    try:
        if not HAS_BIOMCP:
            # Mock implementation if BioMCP SDK is not available
            mock_data = {
                "message": "BioMCP SDK not installed. This is mock data.",
                "pmid": pmid
            }
            return BioMCPResponse(
                data=mock_data,
                format=format,
                query_params={"pmid": pmid, "format": format}
            )
        
        # Get article details
        # fetch_articles expects: (pmids: list[int], full: bool, output_json: bool)
        output_json = format == OutputFormat.JSON
        result = await fetch_articles(
            [int(pmid)],
            full=True,               # return full article where possible
            output_json=output_json,
        )
        
        # Parse result based on format
        if output_json:
            data = json.loads(result)
        else:
            data = result  # Return markdown as-is
        
        return BioMCPResponse(
            data=data,
            format=format,
            query_params={"pmid": pmid, "format": format}
        )
    
    except Exception as e:
        logger.error(f"Error retrieving article details: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving article details: {str(e)}"
        )

# API endpoints for genomic variants
@router.post("/variants/search", response_model=BioMCPResponse)
async def search_genomic_variants(request: VariantSearchRequest):
    """
    Search for genomic variants based on various criteria.
    
    This endpoint uses BioMCP to search for variants matching the specified criteria.
    Results can be returned in either JSON or Markdown format.
    
    Args:
        request: Search parameters for genomic variants
        
    Returns:
        BioMCPResponse: Variants matching the search criteria
    """
    logger.info(
        "Genomic variants search request", 
        extra={
            "gene": request.gene,
            "variant": request.variant,
            "significance": request.significance,
            "size": request.size
        }
    )
    
    try:
        if not HAS_BIOMCP:
            # Mock implementation if BioMCP SDK is not available
            mock_data = {"message": "BioMCP SDK not installed. This is mock data."}
            return BioMCPResponse(
                data=mock_data,
                format=request.format,
                query_params=request.dict(exclude_none=True)
            )
        
        # Convert request parameters to VariantQuery
        query_params = {}
        if request.gene:
            query_params["gene"] = request.gene
        if request.variant:
            query_params["variant"] = request.variant
        if request.chromosome:
            query_params["chromosome"] = request.chromosome
        if request.position:
            query_params["position"] = request.position
        if request.reference:
            query_params["reference"] = request.reference
        if request.alternate:
            query_params["alternate"] = request.alternate
        if request.significance:
            query_params["significance"] = request.significance.value
        if request.condition:
            query_params["condition"] = request.condition
        
        # Add size parameter
        query_params["size"] = request.size
        
        # Create VariantQuery and execute search
        query = VariantQuery(**query_params)
        output_json = request.format == OutputFormat.JSON
        result = await search_variants(query, output_json=output_json)
        
        # Parse result based on format
        if output_json:
            data = json.loads(result)
        else:
            data = result  # Return markdown as-is
        
        return BioMCPResponse(
            data=data,
            format=request.format,
            query_params=request.dict(exclude_none=True)
        )
    
    except Exception as e:
        logger.error(f"Error searching genomic variants: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching genomic variants: {str(e)}"
        )

@router.get("/variants/{variant_id}", response_model=BioMCPResponse)
async def get_variant_details(
    variant_id: str,
    format: OutputFormat = OutputFormat.JSON
):
    """
    Get detailed information about a specific genomic variant.
    
    Args:
        variant_id: Variant identifier
        format: Output format (JSON or Markdown)
        
    Returns:
        BioMCPResponse: Detailed information about the variant
    """
    logger.info(f"Variant details request for ID: {variant_id}")
    
    try:
        if not HAS_BIOMCP:
            # Mock implementation if BioMCP SDK is not available
            mock_data = {
                "message": "BioMCP SDK not installed. This is mock data.",
                "variant_id": variant_id
            }
            return BioMCPResponse(
                data=mock_data,
                format=format,
                query_params={"variant_id": variant_id, "format": format}
            )
        
        # Get variant details
        output_json = format == OutputFormat.JSON
        result = await get_variant(variant_id, output_json=output_json)
        
        # Parse result based on format
        if output_json:
            data = json.loads(result)
        else:
            data = result  # Return markdown as-is
        
        return BioMCPResponse(
            data=data,
            format=format,
            query_params={"variant_id": variant_id, "format": format}
        )
    
    except Exception as e:
        logger.error(f"Error retrieving variant details: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving variant details: {str(e)}"
        )

# Health check endpoint for BioMCP integration
@router.get("/health")
async def biomcp_health_check():
    """
    Health check endpoint to verify BioMCP integration is working.
    
    Returns:
        Dict: Status of BioMCP integration
    """
    status_info = {
        "status": "available" if HAS_BIOMCP else "unavailable",
        "sdk_installed": HAS_BIOMCP,
        "message": "BioMCP integration is ready" if HAS_BIOMCP else "BioMCP SDK is not installed"
    }
    
    # If SDK is installed, try to make a simple API call to verify connectivity
    if HAS_BIOMCP:
        try:
            # Simple test query to verify API connectivity
            test_query = TrialQuery(conditions=["cancer"], page_size=1)
            await search_trials(test_query, output_json=True)
            status_info["api_connectivity"] = "ok"
        except Exception as e:
            status_info["api_connectivity"] = "error"
            status_info["error_message"] = str(e)
    
    return status_info
