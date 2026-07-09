import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.llm_manager import llm_manager
from services.prompt_injection import check_prompt_injection
from services.auth_service import get_current_user
from models.user import User
from rag.pipeline import rag_pipeline
from rag.context_builder import ContextBuilder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm", tags=["llm"])


class ChatRequest(BaseModel):
    messages: list[dict]
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2048


class ChatResponse(BaseModel):
    content: str
    model: str
    model_id: str
    usage: dict


class RAGChatRequest(BaseModel):
    messages: list[dict]
    resume_context: str = ""
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2048


class RAGChatResponse(BaseModel):
    content: str
    model: str
    model_id: str
    usage: dict
    citations: list[dict] = []


def _check_messages_injection(messages: list[dict]):
    for msg in messages:
        content = msg.get("content", "")
        if content:
            is_suspicious, matches, score = check_prompt_injection(content)
            if is_suspicious:
                logger.warning(f"Prompt injection blocked: {matches}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Message blocked by security filter (score={score})",
                )


@router.post("/chat")
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    if not llm_manager.available_models:
        raise HTTPException(status_code=500, detail="No models available")

    _check_messages_injection(request.messages)

    result = llm_manager.chat(
        messages=request.messages,
        model_name=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    if "error" in result and result.get("error"):
        logger.warning(f"LLM chat error: {result['error']}")

    return ChatResponse(
        content=result.get("content", ""),
        model=result.get("model", "unknown"),
        model_id=result.get("model_id", ""),
        usage=result.get("usage", {}),
    )


@router.post("/rag-chat", response_model=RAGChatResponse)
async def rag_chat(request: RAGChatRequest, current_user: User = Depends(get_current_user)):
    if not llm_manager.available_models:
        raise HTTPException(status_code=500, detail="No models available")

    _check_messages_injection(request.messages)

    user_query = ""
    for msg in reversed(request.messages):
        if msg["role"] == "user":
            user_query = msg["content"][:500]
            break

    citations = []
    rag_context = ""
    if user_query:
        try:
            rag_result = rag_pipeline.run(user_query)
            documents = rag_result.get("documents", [])
            if documents:
                for doc in documents[:3]:
                    citations.append({
                        "content": doc.get("content", "")[:300],
                        "score": round(doc.get("rerank_score", doc.get("distance", 0)), 3),
                        "source": doc.get("metadata", {}).get("source", "knowledge base"),
                    })
                rag_context = ContextBuilder.build_context_with_scores(documents, max_chars=3000)
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")

    system_prompt = (
        "You are CV Chacha, a helpful resume coaching assistant in India. "
        "Answer questions about resumes, ATS scoring, job applications, and career advice. "
        "Be friendly, knowledgeable, and practical. "
        "PRIORITIZE the user's actual resume context below (it is the ground truth). "
        "The Retrieved Knowledge section may contain irrelevant demo data — USE IT ONLY IF IT DIRECTLY relates to the user's resume and question. "
        "If retrieved knowledge seems irrelevant or contradicts the resume context, ignore it. "
        "Never fabricate career background. If unsure or if the context lacks relevant information, say so honestly."
    )

    if request.resume_context:
        system_prompt += f"\n\nUser's Resume Context:\n{request.resume_context[:3000]}"
    if rag_context:
        system_prompt += f"\n\nRetrieved Knowledge (may be irrelevant demo data — cross-check with resume context):\n{rag_context}"

    enhanced_messages = [{"role": "system", "content": system_prompt}]
    for msg in request.messages[-10:]:
        enhanced_messages.append(msg)

    result = llm_manager.chat(
        messages=enhanced_messages,
        model_name=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    if "error" in result and result.get("error"):
        logger.warning(f"RAG chat error: {result['error']}")

    return RAGChatResponse(
        content=result.get("content", ""),
        model=result.get("model", "unknown"),
        model_id=result.get("model_id", ""),
        usage=result.get("usage", {}),
        citations=citations,
    )


@router.get("/models")
async def list_models():
    return {
        "models": llm_manager.available_models,
        "current": llm_manager.current_model,
    }


@router.post("/models/switch")
async def switch_model(model_name: str, current_user: User = Depends(get_current_user)):
    success = llm_manager.switch_model(model_name)
    if not success:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model_name}")
    return {"current_model": llm_manager.current_model}


@router.get("/stats")
async def get_stats():
    return llm_manager.get_stats()
