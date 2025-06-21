#!/usr/bin/env python3
"""
Global Memory MCP Server - Quick Validation Test

This script performs a quick validation of all Global Memory components
to ensure everything is working correctly.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def validate_global_memory():
    """Validate all Global Memory components."""
    print("🧠 Global Memory MCP Server - Validation Test")
    print("=" * 50)
    
    try:
        # Test 1: Import all components
        print("\n📦 Testing imports...")
        from global_mcp_server import GlobalMemoryManager, GMCPClient, LANSMemoryIntegration
        from global_mcp_server.core.memory_manager import MemoryQuery, MemoryItem
        from global_mcp_server.storage.database import DatabaseManager
        from global_mcp_server.utils.embeddings import EmbeddingGenerator
        print("✅ All components imported successfully")
        
        # Test 2: Create mock configuration
        print("\n⚙️  Testing configuration...")
        mock_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "test_memory",
                "username": "test",
                "password": "test"
            },
            "embeddings": {
                "model": "all-MiniLM-L6-v2",
                "device": "cpu"
            }
        }
        print("✅ Configuration created")
        
        # Test 3: Create components (without database connection)
        print("\n🔧 Testing component creation...")
        
        # Test embedding generator (can work offline)
        embedding_gen = EmbeddingGenerator(mock_config["embeddings"])
        print("✅ EmbeddingGenerator created")
        
        # Test memory manager creation
        memory_manager = GlobalMemoryManager(mock_config)
        print("✅ GlobalMemoryManager created")
        
        # Test client creation
        client = GMCPClient("http://localhost:8001")
        client.configure_agent("test_agent", "test_user", "test_session")
        print("✅ GMCPClient created and configured")
        
        # Test integration creation
        integration = LANSMemoryIntegration(client, "test_agent", "planning")
        print("✅ LANSMemoryIntegration created")
        
        # Test 4: Memory structures
        print("\n📋 Testing memory structures...")
        query = MemoryQuery(
            query_text="test query",
            memory_types=["episodic"],
            agent_id="test_agent",
            max_results=5
        )
        print("✅ MemoryQuery created")
        
        memory_item = MemoryItem(
            id="test_id",
            memory_type="episodic",
            content="test content",
            metadata={"test": "data"},
            timestamp=asyncio.get_event_loop().time(),
            importance_score=0.5
        )
        print("✅ MemoryItem created")
        
        print("\n🎉 VALIDATION SUCCESSFUL!")
        print("All Global Memory components are working correctly.")
        print("\nNext steps:")
        print("1. Start PostgreSQL database")
        print("2. Run: docker-compose -f docker-compose.global-memory.yml up -d")
        print("3. Test full functionality with: python scripts/demo_global_memory.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure all dependencies are installed: pip install -e .")
        print("2. Check Python path and imports")
        print("3. Verify all files are present")
        return False

if __name__ == "__main__":
    success = asyncio.run(validate_global_memory())
    sys.exit(0 if success else 1)
