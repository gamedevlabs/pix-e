"""
Vector store using sqlite-vec extension.

Provides a separate SQLite database for storing embeddings of
Knowledge Triples and Atomic Facts for similarity retrieval.
"""

import json
import logging
import sqlite3
import struct
from pathlib import Path
from typing import Any, Optional, Union

from django.conf import settings

logger = logging.getLogger(__name__)

# Default path for vector database (separate from main Django DB)
VECTOR_DB_PATH = getattr(
    settings, "VECTOR_DB_PATH", Path(settings.BASE_DIR) / "vectors.db"
)

# Flag to track if sqlite-vec is available
VEC_AVAILABLE = False

# Try to import APSW (preferred) or fall back to sqlite3
try:
    import apsw

    Connection = apsw.Connection
    USING_APSW = True
    ConnectionType = Union[apsw.Connection, sqlite3.Connection]
    logger.debug("Using APSW for SQLite connections")
except ImportError:
    Connection = sqlite3.Connection  # type: ignore
    ConnectionType = Union[sqlite3.Connection, "apsw.Connection"]  # type: ignore
    USING_APSW = False
    logger.warning("APSW not available, falling back to sqlite3")


def get_connection() -> ConnectionType:
    """Get a connection to the vector database with sqlite-vec loaded if available."""
    global VEC_AVAILABLE

    conn: ConnectionType
    if USING_APSW:
        # APSW always supports extensions
        conn = apsw.Connection(str(VECTOR_DB_PATH))
        try:
            # Enable extension loading (APSW requires explicit authorization)
            conn.config(apsw.SQLITE_DBCONFIG_ENABLE_LOAD_EXTENSION, 1)
            import sqlite_vec

            sqlite_vec.load(conn)
            VEC_AVAILABLE = True
            logger.debug("sqlite-vec extension loaded successfully with APSW")
        except ImportError:
            logger.warning("sqlite-vec not installed. Run: pip install sqlite-vec")
            VEC_AVAILABLE = False
        except Exception as e:
            logger.warning(f"Failed to load sqlite-vec: {e}")
            VEC_AVAILABLE = False
    else:
        # Standard sqlite3 - may not support extensions
        conn = sqlite3.connect(str(VECTOR_DB_PATH))
        try:
            conn.enable_load_extension(True)
            import sqlite_vec

            sqlite_vec.load(conn)
            conn.enable_load_extension(False)
            VEC_AVAILABLE = True
            logger.debug("sqlite-vec extension loaded successfully with sqlite3")
        except AttributeError:
            logger.warning(
                "Extension loading not supported. Install APSW: pip install apsw"
            )
            VEC_AVAILABLE = False
        except ImportError:
            logger.warning("sqlite-vec not installed. Run: pip install sqlite-vec")
            VEC_AVAILABLE = False
        except Exception as e:
            logger.warning(f"Failed to load sqlite-vec: {e}")
            VEC_AVAILABLE = False

    return conn


def init_database() -> bool:
    """
    Initialize the vector database schema.

    Returns:
        True if sqlite-vec is available, False if running in fallback mode.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Create table for memory embeddings (metadata storage)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_embeddings (
            id TEXT PRIMARY KEY,
            node_id TEXT NOT NULL,
            chart_id TEXT,
            memory_type TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            embedding BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Create index for faster lookups
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_memory_node_id
        ON memory_embeddings(node_id)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_memory_type
        ON memory_embeddings(memory_type)
    """
    )

    # Create vec0 virtual table for vector similarity search if sqlite-vec available
    if VEC_AVAILABLE:
        try:
            # vec0 syntax: embedding float[dimension]
            # +column for auxiliary columns that can be filtered
            cursor.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_memory USING vec0(
                    embedding float[1536],
                    +node_id TEXT,
                    +memory_type TEXT
                )
            """
            )
            logger.info("Vector database initialized with sqlite-vec support")
        except Exception as e:
            logger.warning(f"Failed to create vec0 table: {e}")
    else:
        logger.info(
            "Vector database initialized in fallback mode (no vec). "
            "Vector similarity search will not be available."
        )

    # APSW auto-commits, sqlite3 needs explicit commit
    if not USING_APSW and hasattr(conn, "commit"):
        conn.commit()  # type: ignore[union-attr]
    conn.close()
    return VEC_AVAILABLE


def serialize_embedding(embedding: list[float]) -> bytes:
    """Serialize embedding list to bytes for storage."""
    return struct.pack(f"{len(embedding)}f", *embedding)


def deserialize_embedding(data: bytes) -> list[float]:
    """Deserialize bytes back to embedding list."""
    count = len(data) // 4  # 4 bytes per float
    return list(struct.unpack(f"{count}f", data))


def embedding_to_json(embedding: list[float]) -> str:
    """Convert embedding to JSON string for vec0 queries."""
    return json.dumps(embedding)


class VectorStore:
    """Interface for storing and querying memory embeddings."""

    def __init__(self) -> None:
        self._conn: Optional[ConnectionType] = None

    @property
    def conn(self) -> ConnectionType:
        if self._conn is None:
            self._conn = get_connection()
        return self._conn

    @property
    def vec_enabled(self) -> bool:
        """Check if sqlite-vec is available."""
        # Ensure connection is established to set VEC_AVAILABLE flag
        _ = self.conn
        return VEC_AVAILABLE

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def store_memory(
        self,
        memory_id: str,
        node_id: str,
        memory_type: str,
        content: str,
        embedding: list[float],
        chart_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Store a memory with its embedding."""
        cursor = self.conn.cursor()

        # Store metadata and embedding in main table
        metadata_json = json.dumps(metadata) if metadata else None
        embedding_bytes = serialize_embedding(embedding)

        cursor.execute(
            """
            INSERT OR REPLACE INTO memory_embeddings
            (id, node_id, chart_id, memory_type, content, metadata, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                memory_id,
                node_id,
                chart_id,
                memory_type,
                content,
                metadata_json,
                embedding_bytes,
            ),
        )

        # Also store in vec0 table if available
        if VEC_AVAILABLE:
            try:
                # Get the rowid of the inserted/updated row
                cursor.execute(
                    "SELECT rowid FROM memory_embeddings WHERE id = ?",
                    (memory_id,),
                )
                row = cursor.fetchone()
                if row:
                    rowid = row[0]
                    # vec0 doesn't support INSERT OR REPLACE, so delete first
                    cursor.execute(
                        "DELETE FROM vec_memory WHERE rowid = ?",
                        (rowid,),
                    )
                    # vec0 uses JSON for embedding input
                    embedding_json = embedding_to_json(embedding)
                    cursor.execute(
                        """
                        INSERT INTO vec_memory
                        (rowid, embedding, node_id, memory_type)
                        VALUES (?, ?, ?, ?)
                    """,
                        (rowid, embedding_json, node_id, memory_type),
                    )
            except Exception as e:
                logger.warning(f"Failed to store in vec0 table: {e}")

        # APSW auto-commits, sqlite3 needs explicit commit
        if not USING_APSW and hasattr(self.conn, "commit"):
            self.conn.commit()  # type: ignore[union-attr]

    def search_similar(
        self,
        query_embedding: list[float],
        limit: int = 10,
        memory_type: Optional[str] = None,
        node_ids: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar memories using vector similarity (KNN).

        Uses sqlite-vec's MATCH operator for KNN search.
        If sqlite-vec is not available, returns an empty list with a warning.
        """
        if not VEC_AVAILABLE:
            logger.warning(
                "Vector similarity search unavailable. "
                "Install sqlite-vec: pip install sqlite-vec"
            )
            return []

        cursor = self.conn.cursor()
        query_json = embedding_to_json(query_embedding)

        # Build KNN query using vec0's MATCH syntax
        # Note: Cannot filter on vec0 auxiliary columns in WHERE clause
        # Must filter on the joined memory_embeddings table instead

        # Build WHERE conditions for filtering on memory_embeddings
        where_conditions = []
        params: list[Any] = [query_json, limit]

        if memory_type:
            where_conditions.append("m.memory_type = ?")
            params.append(memory_type)

        if node_ids:
            placeholders = ",".join("?" * len(node_ids))
            where_conditions.append(f"m.node_id IN ({placeholders})")
            params.extend(node_ids)

        # Build the query
        where_clause = ""
        if where_conditions:
            where_clause = " AND " + " AND ".join(where_conditions)

        query = f"""
            SELECT
                m.id,
                m.node_id,
                m.chart_id,
                m.memory_type,
                m.content,
                m.metadata,
                v.distance
            FROM vec_memory v
            JOIN memory_embeddings m ON v.rowid = m.rowid
            WHERE v.embedding MATCH ?
              AND v.k = ?{where_clause}
            ORDER BY v.distance
        """

        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            return []

        results = []
        for row in rows:
            result = {
                "id": row[0],
                "node_id": row[1],
                "chart_id": row[2],
                "memory_type": row[3],
                "content": row[4],
                "metadata": json.loads(str(row[5])) if row[5] else None,
                "distance": row[6],
            }
            results.append(result)

        return results

    def get_memories_by_node(
        self,
        node_id: str,
        memory_type: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get all memories for a specific node."""
        cursor = self.conn.cursor()

        query = (
            "SELECT id, node_id, chart_id, memory_type, content, metadata "
            "FROM memory_embeddings WHERE node_id = ?"
        )
        params: list[Any] = [node_id]

        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "node_id": row[1],
                "chart_id": row[2],
                "memory_type": row[3],
                "content": row[4],
                "metadata": json.loads(str(row[5])) if row[5] else None,
            }
            for row in rows
        ]

    def delete_memories_by_node(self, node_id: str) -> int:
        """Delete all memories for a node. Returns count deleted."""
        cursor = self.conn.cursor()

        # Get rowids to delete
        cursor.execute(
            "SELECT rowid FROM memory_embeddings WHERE node_id = ?", (node_id,)
        )
        rowids = [row[0] for row in cursor.fetchall()]

        if rowids:
            # Delete from vec0 table if available
            if VEC_AVAILABLE:
                try:
                    placeholders = ",".join("?" * len(rowids))
                    cursor.execute(
                        f"DELETE FROM vec_memory WHERE rowid IN ({placeholders})",
                        rowids,
                    )
                except Exception as e:
                    logger.warning(f"Failed to delete from vec0 table: {e}")

            # Delete from main table
            cursor.execute(
                "DELETE FROM memory_embeddings WHERE node_id = ?", (node_id,)
            )

        # APSW auto-commits, sqlite3 needs explicit commit
        if not USING_APSW and hasattr(self.conn, "commit"):
            self.conn.commit()  # type: ignore[union-attr]
        return len(rowids)
