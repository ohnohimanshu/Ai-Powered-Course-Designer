import os
import pickle
import logging
import numpy as np
from django.conf import settings
from ai_engine.services import EmbeddingService

logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    Manages FAISS vector index for semantic search.
    Stores index on disk in settings.AI_ENGINE['VECTOR_STORE_PATH'].
    """
    _index = None
    _id_map = {}  # Maps FAISS ID -> ResourceChunk ID (DB ID)
    
    INDEX_FILE = "faiss_index.bin"
    MAP_FILE = "index_map.pkl"

    @classmethod
    def get_store_path(cls):
        path = settings.AI_ENGINE['VECTOR_STORE_PATH']
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def get_index(cls):
        """Loads index from disk or creates new one."""
        if cls._index is None:
            try:
                import faiss
                path = cls.get_store_path()
                index_path = os.path.join(path, cls.INDEX_FILE)
                map_path = os.path.join(path, cls.MAP_FILE)

                if os.path.exists(index_path) and os.path.exists(map_path):
                    logger.info("Loading vector store from disk...")
                    cls._index = faiss.read_index(index_path)
                    with open(map_path, 'rb') as f:
                        cls._id_map = pickle.load(f)
                else:
                    logger.info("Creating new vector store...")
                    # Dimension 384 for all-MiniLM-L6-v2
                    dimension = 384 
                    cls._index = faiss.IndexFlatL2(dimension)
                    cls._id_map = {}
            except ImportError:
                logger.error("faiss-cpu not installed")
                raise

        return cls._index

    @classmethod
    def save_index(cls):
        """Persists index to disk."""
        if cls._index is None:
            return

        import faiss
        path = cls.get_store_path()
        faiss.write_index(cls._index, os.path.join(path, cls.INDEX_FILE))
        with open(os.path.join(path, cls.MAP_FILE), 'wb') as f:
            pickle.dump(cls._id_map, f)
        logger.info("Vector store saved.")

    @classmethod
    def add_texts(cls, texts, metadatas):
        """
        Generates embeddings for texts and adds to index.
        Args:
            texts: list of strings
            metadatas: list of dicts (must contain 'chunk_id')
        """
        if not texts:
            return

        # Batch generation
        vectors = EmbeddingService.generate_embedding(texts)
        cls.add_vectors(vectors, metadatas)

    @classmethod
    def add_vectors(cls, vectors, metadatas):
        """
        Adds vectors to FAISS.
        Args:
            vectors: list of list of floats
            metadatas: list of dicts with 'chunk_id'
        """
        index = cls.get_index()
        vectors_np = np.array(vectors).astype('float32')
        
        start_id = index.ntotal
        index.add(vectors_np)
        
        # Update ID map
        for i, meta in enumerate(metadatas):
            faiss_id = start_id + i
            cls._id_map[faiss_id] = meta['chunk_id']
        
        cls.save_index()

    @classmethod
    def search(cls, query_text, k=5):
        """
        Search for similar chunks.
        Returns: list of valid chunk_ids
        """
        index = cls.get_index()
        if index.ntotal == 0:
            return []

        query_vec = EmbeddingService.generate_embedding(query_text)
        query_np = np.array([query_vec]).astype('float32')
        
        distances, indices = index.search(query_np, k)
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx in cls._id_map:
                results.append(cls._id_map[idx])
        
        return results
