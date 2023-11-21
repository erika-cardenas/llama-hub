"""Weaviate Sub-Question Query Engine Pack."""


from typing import Any, Dict, List, Optional

from llama_index.indices.vector_store import VectorStoreIndex
from llama_index.llama_pack.base import BaseLlamaPack
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.schema import TextNode
from llama_index.storage.storage_context import StorageContext
from llama_index.vector_stores.weaviate import WeaviateVectorStore
from llama_index.vector_stores.types import VectorStoreInfo
from llama_index.tools import QueryEngineTool, ToolMetadata
from llama_index.query_engine import SubQuestionQueryEngine


class WeaviateSubQuestion(BaseLlamaPack):
    """Weaviate Sub-Question query engine pack."""

    def __init__(
        self,
        collection_name: str,
        vector_store_info: VectorStoreInfo,
        host: str,
        auth_client_secret: str,
        nodes: Optional[List[TextNode]] = None,
        **kwargs: Any,
    ) -> None:
        """Init params."""
        from weaviate import Client  # noqa: F401

        self.client: Client = Client(host, auth_client_secret=auth_client_secret)
        
        import weaviate

        weaviate_client = self.client 
        weaviate_collection = weaviate_client.get_or_create_collection(collection_name)

        self._vector_store = WeaviateVectorStore(weaviate_collection=weaviate_collection)
        
        if nodes is not None:
            self._storage_context = StorageContext.from_defaults(
                vector_store=self._vector_store
            )
            self._index = VectorStoreIndex(nodes, storage_context=self._storage_context, **kwargs)
        else:
            self._index = VectorStoreIndex.from_vector_store(self._vector_store, **kwargs)
            self._storage_context = self._index.storage_context

        self.retriever = self._index.as_retriever()

        query_engine = self._index.as_query_engine()
        query_engine_tools = [
            QueryEngineTool(
                query_engine = query_engine,
                metadata = ToolMetadata(name='Vector Index')
            )
        ]
        self.query_engine = SubQuestionQueryEngine.from_defaults(query_engine_tools=query_engine_tools)

    def get_modules(self) -> Dict[str, Any]:
        """Get modules."""
        return {
            "vector_store": self._vector_store,
            "storage_context": self._storage_context,
            "index": self._index,
            "retriever": self.retriever,
            "query_engine": self.query_engine,
        }

    def retrieve(self, query_str: str) -> Any:
        """Retrieve."""
        return self.retriever.retrieve(query_str)

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the pipeline."""
        return self.query_engine.query(*args, **kwargs)
