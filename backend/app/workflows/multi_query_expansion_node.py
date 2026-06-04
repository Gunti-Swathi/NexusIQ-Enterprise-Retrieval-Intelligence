from typing import Any


class MultiQueryExpansionNode:
    def __init__(self, llm: Any) -> None:
        self.llm = llm

    async def run(self, user_query: str, use_multi_query: bool, should_expand_query: bool = True) -> dict:
        if not use_multi_query or not should_expand_query:
            return {"expanded_queries": [user_query]}
        expanded = await self.llm.expand_queries(user_query, count=3)
        queries = list(dict.fromkeys([user_query, *expanded]))
        return {"expanded_queries": queries}
