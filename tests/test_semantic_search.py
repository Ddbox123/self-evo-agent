#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 8.5 单元测试 - 向量语义搜索模块
"""

import pytest
import sys
import os
from pathlib import Path

test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(test_dir)
sys.path.insert(0, project_root)

from core.semantic_search import (
    SemanticEntry, SearchResult, EmbeddingService, VectorStore,
    SemanticMemory, SemanticSearchService,
    get_semantic_search, reset_semantic_search,
)


class TestSemanticEntry:
    def test_create_entry(self):
        entry = SemanticEntry(
            entry_id="test_001",
            content="Test content",
            content_type="memory",
            embedding=[0.1] * 128,
        )
        assert entry.entry_id == "test_001"
        assert entry.content == "Test content"

    def test_to_dict(self):
        entry = SemanticEntry(
            entry_id="test_002",
            content="Test content",
            content_type="knowledge",
            embedding=[0.5] * 128,
            tags=["test"],
        )
        d = entry.to_dict()
        assert d["entry_id"] == "test_002"
        assert d["content_type"] == "knowledge"


class TestEmbeddingService:
    def test_init(self):
        service = EmbeddingService()
        assert service.model_name == "simple"

    def test_encode(self):
        service = EmbeddingService()
        vec1 = service.encode("Hello world")
        vec2 = service.encode("Hello world")
        assert len(vec1) == 128
        assert vec1 == vec2

    def test_encode_different_texts(self):
        service = EmbeddingService()
        vec1 = service.encode("Python programming")
        vec2 = service.encode("JavaScript programming")
        assert vec1 != vec2

    def test_cache(self):
        service = EmbeddingService()
        vec1 = service.encode("Cached text")
        vec2 = service.encode("Cached text")
        assert vec1 == vec2
        assert len(service._cache) == 1

    def test_encode_batch(self):
        service = EmbeddingService()
        texts = ["text1", "text2", "text3"]
        vectors = service.encode_batch(texts)
        assert len(vectors) == 3
        assert all(len(v) == 128 for v in vectors)


class TestVectorStore:
    def test_init(self, tmp_path):
        store = VectorStore(str(tmp_path / "vector.json"))
        assert store.storage_path.parent.exists()

    def test_add_entry(self, tmp_path):
        store = VectorStore(str(tmp_path / "vector.json"))
        entry = SemanticEntry(
            entry_id="vtest_001",
            content="Test entry",
            content_type="memory",
            embedding=[0.1] * 128,
        )
        store.add(entry)
        retrieved = store.get("vtest_001")
        assert retrieved is not None
        assert retrieved.content == "Test entry"

    def test_remove_entry(self, tmp_path):
        store = VectorStore(str(tmp_path / "vector.json"))
        entry = SemanticEntry(
            entry_id="vtest_002",
            content="Entry to remove",
            content_type="test",
            embedding=[0.2] * 128,
        )
        store.add(entry)
        assert store.remove("vtest_002") is True
        assert store.get("vtest_002") is None

    def test_search(self, tmp_path):
        store = VectorStore(str(tmp_path / "vector.json"))
        service = EmbeddingService()

        entry1 = SemanticEntry(
            entry_id="search_001",
            content="Python programming tutorial",
            content_type="tutorial",
            embedding=service.encode("Python programming tutorial"),
        )
        entry2 = SemanticEntry(
            entry_id="search_002",
            content="JavaScript web development",
            content_type="tutorial",
            embedding=service.encode("JavaScript web development"),
        )

        store.add(entry1)
        store.add(entry2)

        query = service.encode("Python code")
        results = store.search(query, limit=5)
        assert len(results) >= 1

    def test_count(self, tmp_path):
        store = VectorStore(str(tmp_path / "vector.json"))
        for i in range(5):
            entry = SemanticEntry(
                entry_id=f"count_{i}",
                content=f"Content {i}",
                content_type="test",
                embedding=[0.1] * 128,
            )
            store.add(entry)
        assert store.count() == 5


class TestSemanticMemory:
    def test_init(self, tmp_path):
        memory = SemanticMemory(str(tmp_path / "memory.json"))
        assert memory.embedding_service is not None
        assert memory.vector_store is not None

    def test_add_memory(self, tmp_path):
        memory = SemanticMemory(str(tmp_path / "memory.json"))
        memory_id = memory.add_memory("Test memory content", "memory")
        assert memory_id is not None
        retrieved = memory.get_memory(memory_id)
        assert retrieved is not None
        assert retrieved.content == "Test memory content"

    def test_search_memories(self, tmp_path):
        memory = SemanticMemory(str(tmp_path / "memory.json"))
        memory.add_memory("Python is great", "experience")
        memory.add_memory("JavaScript is versatile", "experience")

        results = memory.search_memories("Python programming", limit=5)
        assert isinstance(results, list)

    def test_delete_memory(self, tmp_path):
        memory = SemanticMemory(str(tmp_path / "memory.json"))
        memory_id = memory.add_memory("To be deleted", "test")
        assert memory.delete_memory(memory_id) is True
        assert memory.get_memory(memory_id) is None

    def test_statistics(self, tmp_path):
        memory = SemanticMemory(str(tmp_path / "memory.json"))
        memory.add_memory("Content 1", "memory")
        memory.add_memory("Content 2", "knowledge")
        memory.add_memory("Content 3", "memory")

        stats = memory.get_statistics()
        assert stats["total_memories"] == 3
        assert stats["by_content_type"]["memory"] == 2


class TestSemanticSearchService:
    def test_init(self, tmp_path):
        service = SemanticSearchService(str(tmp_path / "search.json"))
        assert service.embedding_service is not None
        assert service.semantic_memory is not None

    def test_add(self, tmp_path):
        service = SemanticSearchService(str(tmp_path / "search.json"))
        item_id = service.add("New semantic item", "document")
        assert item_id is not None

    def test_search(self, tmp_path):
        service = SemanticSearchService(str(tmp_path / "search.json"))
        service.add("Python tutorial", "tutorial")
        service.add("Java tutorial", "tutorial")

        results = service.search("Python programming", limit=5)
        assert isinstance(results, list)

    def test_search_experiences(self, tmp_path):
        service = SemanticSearchService(str(tmp_path / "search.json"))
        service.add("Learned Python", "experience")
        results = service.search_experiences("Python learning")
        assert isinstance(results, list)

    def test_search_knowledge(self, tmp_path):
        service = SemanticSearchService(str(tmp_path / "search.json"))
        service.add("Python facts", "knowledge")
        results = service.search_knowledge("Python information")
        assert isinstance(results, list)

    def test_get_context_for_task(self, tmp_path):
        service = SemanticSearchService(str(tmp_path / "search.json"))
        service.add("Solution to bug X", "experience")
        service.add("Approach to refactoring", "experience")

        context = service.get_context_for_task("How to fix bug X", max_memories=2)
        assert isinstance(context, str)


class TestIntegration:
    def test_singleton(self, tmp_path):
        service1 = get_semantic_search(str(tmp_path / "s1.json"))
        service2 = get_semantic_search(str(tmp_path / "s1.json"))
        assert service1 is service2

        reset_semantic_search()
        service3 = get_semantic_search(str(tmp_path / "s1.json"))
        assert service3 is not service1


@pytest.fixture(autouse=True)
def cleanup(tmp_path):
    yield
    reset_semantic_search()
