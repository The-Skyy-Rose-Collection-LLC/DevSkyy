#!/usr/bin/env python3
"""
Pinecone Vector Database Setup and Management

This script helps you:
1. Verify Pinecone API connection
2. List existing indexes
3. Create a new index for DevSkyy
4. Test vector operations
5. Get usage statistics

Usage:
    python scripts/pinecone_setup.py verify
    python scripts/pinecone_setup.py list-indexes
    python scripts/pinecone_setup.py create-index
    python scripts/pinecone_setup.py test
    python scripts/pinecone_setup.py stats
"""

import os
import sys

from dotenv import load_dotenv


# Load environment variables
load_dotenv()

try:
    from pinecone import Pinecone, ServerlessSpec
except ImportError:
    print("❌ Error: pinecone-client package not installed")
    print("Install with: pip install pinecone-client~=5.0.1")
    sys.exit(1)


class PineconeManager:
    """Manage Pinecone vector database operations."""

    def __init__(self):
        """Initialize Pinecone client."""
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "devskyy")

        if not self.api_key:
            raise ValueError(
                "❌ Configuration Error: PINECONE_API_KEY not set in environment.\n"
                "Get your API key from: https://app.pinecone.io/"
            )

        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)

    def verify_connection(self):
        """Verify Pinecone API connection."""
        print("\n" + "=" * 80)
        print("PINECONE CONNECTION VERIFICATION")
        print("=" * 80 + "\n")

        try:
            # List indexes to verify connection
            indexes = self.pc.list_indexes()

            print("✅ Successfully connected to Pinecone!")
            print("📊 API Key configured (redacted for security)")
            print(f"🌍 Environment: {self.environment}")
            print(f"📁 Default Index Name: {self.index_name}")
            print(f"📋 Total Indexes: {len(indexes.names())}")

            if indexes.names():
                print("\n📚 Available Indexes:")
                for idx in indexes.names():
                    print(f"   • {idx}")
            else:
                print("\n⚠️  No indexes found. Run 'create-index' to create one.")

            return True

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("\nTroubleshooting:")
            print("1. Verify API key is correct: https://app.pinecone.io/")
            print("2. Check your internet connection")
            print("3. Ensure Pinecone service is available")
            return False

    def list_indexes(self):
        """List all Pinecone indexes."""
        print("\n" + "=" * 80)
        print("PINECONE INDEXES")
        print("=" * 80 + "\n")

        try:
            indexes = self.pc.list_indexes()

            if not indexes.names():
                print("⚠️  No indexes found.")
                print("Create one with: python scripts/pinecone_setup.py create-index")
                return

            for idx_name in indexes.names():
                print(f"\n📁 Index: {idx_name}")
                try:
                    # Get index description
                    index = self.pc.Index(idx_name)
                    stats = index.describe_index_stats()

                    print(f"   Dimensions: {stats.get('dimension', 'N/A')}")
                    print(f"   Total Vectors: {stats.get('total_vector_count', 0):,}")
                    print(f"   Namespaces: {len(stats.get('namespaces', {}))}")

                    # Show namespaces
                    if stats.get('namespaces'):
                        print("   Namespaces:")
                        for ns, ns_stats in stats['namespaces'].items():
                            print(f"      • {ns}: {ns_stats.get('vector_count', 0):,} vectors")

                except Exception as e:
                    print(f"   ⚠️  Could not get stats: {e}")

        except Exception as e:
            print(f"❌ Error listing indexes: {e}")

    def create_index(
        self,
        index_name: str | None = None,
        dimension: int = 1536,  # OpenAI ada-002 embedding size
        metric: str = "cosine"
    ):
        """
        Create a new Pinecone index.

        Args:
            index_name: Name of the index (default: from env)
            dimension: Vector dimension (default: 1536 for OpenAI embeddings)
            metric: Distance metric (cosine, euclidean, dotproduct)
        """
        index_name = index_name or self.index_name

        print("\n" + "=" * 80)
        print(f"CREATE PINECONE INDEX: {index_name}")
        print("=" * 80 + "\n")

        try:
            # Check if index already exists
            existing_indexes = self.pc.list_indexes().names()
            if index_name in existing_indexes:
                print(f"⚠️  Index '{index_name}' already exists!")
                response = input("\nDo you want to delete and recreate it? (yes/no): ")
                if response.lower() != 'yes':
                    print("❌ Index creation cancelled.")
                    return False

                print(f"🗑️  Deleting existing index '{index_name}'...")
                self.pc.delete_index(index_name)
                print("✅ Index deleted.")

            # Create index
            print("\n📝 Creating index with configuration:")
            print(f"   Name: {index_name}")
            print(f"   Dimension: {dimension}")
            print(f"   Metric: {metric}")
            print("   Cloud: GCP")
            print("   Region: us-central1")

            self.pc.create_index(
                name=index_name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(
                    cloud='gcp',
                    region='us-central1'
                )
            )

            print("\n✅ Index created successfully!")
            print(f"📁 Index Name: {index_name}")
            print("🌍 Access via: Pinecone dashboard")
            print("🔗 URL: https://app.pinecone.io/")

            return True

        except Exception as e:
            print(f"❌ Error creating index: {e}")
            return False

    def test_operations(self):
        """Test basic vector operations."""
        print("\n" + "=" * 80)
        print(f"TEST VECTOR OPERATIONS: {self.index_name}")
        print("=" * 80 + "\n")

        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes().names()
            if self.index_name not in existing_indexes:
                print(f"❌ Index '{self.index_name}' does not exist.")
                print("Create it with: python scripts/pinecone_setup.py create-index")
                return False

            # Connect to index
            index = self.pc.Index(self.index_name)

            # Test data (1536 dimensions for OpenAI embeddings)
            test_vectors = [
                {
                    "id": "test-vector-1",
                    "values": [0.1] * 1536,
                    "metadata": {"text": "Test document 1", "source": "test"}
                },
                {
                    "id": "test-vector-2",
                    "values": [0.2] * 1536,
                    "metadata": {"text": "Test document 2", "source": "test"}
                }
            ]

            print("1️⃣  Upserting test vectors...")
            index.upsert(vectors=test_vectors, namespace="test")
            print("✅ Vectors upserted successfully!")

            print("\n2️⃣  Querying vectors...")
            query_response = index.query(
                vector=[0.1] * 1536,
                top_k=2,
                namespace="test",
                include_metadata=True
            )
            print(f"✅ Query successful! Found {len(query_response['matches'])} matches")

            for i, match in enumerate(query_response['matches']):
                print(f"\n   Match {i+1}:")
                print(f"      ID: {match['id']}")
                print(f"      Score: {match['score']:.4f}")
                print(f"      Metadata: {match.get('metadata', {})}")

            print("\n3️⃣  Getting index stats...")
            stats = index.describe_index_stats()
            print(f"✅ Total vectors: {stats.get('total_vector_count', 0):,}")

            print("\n4️⃣  Cleaning up test vectors...")
            index.delete(ids=["test-vector-1", "test-vector-2"], namespace="test")
            print("✅ Test vectors deleted!")

            print("\n" + "=" * 80)
            print("✅ ALL TESTS PASSED!")
            print("=" * 80)

            return True

        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_stats(self):
        """Get Pinecone usage statistics."""
        print("\n" + "=" * 80)
        print("PINECONE USAGE STATISTICS")
        print("=" * 80 + "\n")

        try:
            indexes = self.pc.list_indexes()

            if not indexes.names():
                print("⚠️  No indexes found.")
                return

            total_vectors = 0
            total_dimensions = 0

            for idx_name in indexes.names():
                try:
                    index = self.pc.Index(idx_name)
                    stats = index.describe_index_stats()

                    vectors = stats.get('total_vector_count', 0)
                    dimension = stats.get('dimension', 0)

                    total_vectors += vectors
                    total_dimensions += dimension

                    print(f"📁 {idx_name}")
                    print(f"   Vectors: {vectors:,}")
                    print(f"   Dimension: {dimension}")
                    print(f"   Storage: ~{(vectors * dimension * 4 / 1024 / 1024):.2f} MB")
                    print()

                except Exception as e:
                    print(f"   ⚠️  Error: {e}\n")

            print("=" * 80)
            print(f"📊 Total Vectors: {total_vectors:,}")
            print(f"📏 Total Dimensions: {total_dimensions:,}")
            print(f"💾 Estimated Storage: ~{(total_vectors * 1536 * 4 / 1024 / 1024):.2f} MB")
            print("=" * 80)

        except Exception as e:
            print(f"❌ Error getting stats: {e}")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    try:
        manager = PineconeManager()

        if command == "verify":
            manager.verify_connection()
        elif command == "list-indexes":
            manager.list_indexes()
        elif command == "create-index":
            manager.create_index()
        elif command == "test":
            manager.test_operations()
        elif command == "stats":
            manager.get_stats()
        elif command == "help":
            print(__doc__)
        else:
            print(f"❌ Unknown command: {command}")
            print(__doc__)
            sys.exit(1)

    except ValueError as e:
        print(f"\n{e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
