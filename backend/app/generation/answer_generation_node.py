import re
from typing import Any


class AnswerGenerationNode:
    def __init__(self, llm: Any) -> None:
        self.llm = llm

    async def run(self, user_query: str, chunks: list[dict]) -> dict:
        if not chunks:
            answer = "I do not have enough grounded context in the uploaded documents to answer that."
            return {"generated_answer": answer, "answer": answer, "citations": []}
        source_by_document_id = {}
        for chunk in chunks:
            if chunk["document_id"] not in source_by_document_id:
                source_by_document_id[chunk["document_id"]] = len(source_by_document_id) + 1
            chunk["source_number"] = source_by_document_id[chunk["document_id"]]
        context = "\n\n".join(
            f"[{chunk['source_number']}] Chunk {chunk['chunk_index']}\n{chunk['text']}"
            for chunk in chunks
        )
        prompt = f"""
You are an enterprise document search assistant.
Answer only from the provided context.
If the context does not contain the answer, say you do not have enough grounded context.
Keep the answer concise, professional, and directly useful to a non-technical user.
If the user asks which model, method, tool, or technique was used, name the specific model first, then briefly explain how it is generally used for the prediction task.
Do not list unrelated models or documents.
Every factual claim must be supported with source citations in the form [1] or [1,2].
Every technical claim, comparison claim, method description, dataset statement, model statement, and result statement must include a citation marker from the retrieved evidence.
Avoid unsupported claims. If evidence is missing, say that the indexed documents do not provide enough support.
Do not cite filenames or chunk ids in the answer text.

Question:
{user_query}

Context:
{context}

Grounded answer:
""".strip()
        answer = (await self.llm.generate(prompt, temperature=0.0)).strip()
        citations_by_document = {}
        for chunk in chunks:
            citation = citations_by_document.setdefault(
                chunk["document_id"],
                {
                    "source_number": chunk["source_number"],
                    "file_name": chunk["filename"],
                    "document_id": chunk["document_id"],
                    "chunk_indices": [],
                    "chunk_ids": [],
                    "page_number": None,
                },
            )
            citation["chunk_indices"].append(chunk["chunk_index"])
            citation["chunk_ids"].append(chunk["id"])
            metadata = chunk.get("metadata") if isinstance(chunk.get("metadata"), dict) else {}
            if citation["page_number"] is None:
                citation["page_number"] = metadata.get("page_number")
        citations = [
            {
                **citation,
                "chunk_indices": sorted(set(citation["chunk_indices"])),
                "chunk_ids": sorted(set(citation["chunk_ids"])),
            }
            for citation in sorted(citations_by_document.values(), key=lambda item: item["source_number"])
        ]
        answer, citations = _keep_only_answer_citations(answer, citations)
        return {"generated_answer": answer, "answer": answer, "citations": citations}


def _keep_only_answer_citations(answer: str, citations: list[dict]) -> tuple[str, list[dict]]:
    cited_numbers = []
    for citation_group in re.findall(r"\[([0-9,\s]+)\]", answer):
        for value in citation_group.split(","):
            value = value.strip()
            if value.isdigit():
                cited_numbers.append(int(value))

    if not cited_numbers:
        return answer, citations[:1]

    used_numbers = []
    for number in cited_numbers:
        if number not in used_numbers:
            used_numbers.append(number)

    citation_by_number = {citation["source_number"]: citation for citation in citations}
    filtered = [citation_by_number[number] for number in used_numbers if number in citation_by_number]
    if not filtered:
        return answer, citations[:1]

    remap = {citation["source_number"]: index + 1 for index, citation in enumerate(filtered)}

    def replace_group(match: re.Match) -> str:
        values = []
        for value in match.group(1).split(","):
            value = value.strip()
            if value.isdigit() and int(value) in remap:
                values.append(str(remap[int(value)]))
        return f"[{','.join(values)}]" if values else ""

    renumbered_answer = re.sub(r"\[([0-9,\s]+)\]", replace_group, answer)
    renumbered_citations = [
        {**citation, "source_number": remap[citation["source_number"]]}
        for citation in filtered
    ]
    return renumbered_answer, renumbered_citations
