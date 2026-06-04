from app.workflows.query_processing_node import QueryProcessingNode


class RouterAgent(QueryProcessingNode):
    async def route(self, question: str) -> str:
        result = await self.run(question)
        return result["route"]
