import logging

logger = logging.getLogger(__name__)


class ContextBuilder:

    @staticmethod
    def build_context(
        documents: list[str],
        max_chars: int = 4000,
        separator: str = "\n\n---\n\n"
    ) -> str:
        context_parts = []
        total = 0

        for doc in documents:
            if total + len(doc) > max_chars:
                remaining = max_chars - total
                if remaining > 100:
                    context_parts.append(doc[:remaining])
                break
            context_parts.append(doc)
            total += len(doc) + len(separator)

        return separator.join(context_parts)

    @staticmethod
    def build_context_with_scores(
        results: list[dict],
        max_chars: int = 4000,
        include_scores: bool = True
    ) -> str:
        context_parts = []
        total = 0

        for r in results:
            content = r["content"]
            if include_scores:
                score = r.get("rerank_score", r.get("distance", 0))
                header = f"[Relevance: {score:.3f}]"
                entry = f"{header}\n{content}"
            else:
                entry = content

            if total + len(entry) > max_chars:
                remaining = max_chars - total
                if remaining > 100:
                    if include_scores:
                        context_parts.append(entry[:remaining])
                    else:
                        context_parts.append(content[:remaining])
                break

            context_parts.append(entry)
            total += len(entry) + 80

        return "\n\n---\n\n".join(context_parts)

    @staticmethod
    def format_for_prompt(context: str, query: str) -> str:
        return f"""Use the following context to answer the user's question.

Context:
{context}

Question: {query}

Answer based on the context above. If the context doesn't contain relevant information, say so."""
