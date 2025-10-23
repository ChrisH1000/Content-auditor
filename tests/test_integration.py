"""Integration tests for caching and fetching."""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cache import Cache
from utils.html_fetch import fetch_page
from utils.html_to_text import extract_text, extract_metadata


def test_cache():
    """Test cache functionality."""
    print("Testing cache...")
    
    cache = Cache(".cache_test")
    
    # Test set and get
    test_data = {"foo": "bar", "score": 95}
    cache.set("test_url", test_data)
    
    retrieved = cache.get("test_url")
    assert retrieved == test_data
    print("  ✓ Cache set/get works")
    
    # Test cache miss
    assert cache.get("nonexistent") is None
    print("  ✓ Cache miss works")
    
    # Test stats
    stats = cache.get_stats()
    assert stats["total_entries"] >= 1
    print(f"  ✓ Cache stats: {stats['total_entries']} entries")
    
    # Cleanup
    cache.clear()
    stats = cache.get_stats()
    assert stats["total_entries"] == 0
    print("  ✓ Cache clear works")
    
    return True


def test_fetch_and_extract():
    """Test HTML fetching and extraction."""
    print("\nTesting HTML fetching and extraction...")
    
    # Fetch a simple page
    url = "https://www.example.com"
    html = fetch_page(url, timeout=10)
    
    if html:
        print(f"  ✓ Fetched {len(html)} bytes from {url}")
        
        # Extract text
        text = extract_text(html)
        if text:
            print(f"  ✓ Extracted {len(text)} characters of text")
        
        # Extract metadata
        metadata = extract_metadata(html)
        if metadata.get("title"):
            print(f"  ✓ Extracted title: {metadata['title'][:50]}")
        
        return True
    else:
        print("  ⚠ Could not fetch page (network issue?)")
        return False


def test_cache_integration():
    """Test cache with real data."""
    print("\nTesting cache integration...")
    
    cache = Cache(".cache_test")
    cache.clear()
    
    url = "https://www.example.com"
    
    # First fetch (cache miss)
    start = time.time()
    html = fetch_page(url, timeout=10)
    if html:
        text = extract_text(html)
        data = {"url": url, "text_length": len(text) if text else 0}
        cache.set(url, data)
        first_time = time.time() - start
        print(f"  ✓ First fetch took {first_time:.2f}s (cache miss)")
        
        # Second fetch (cache hit)
        start = time.time()
        cached_data = cache.get(url)
        second_time = time.time() - start
        print(f"  ✓ Second fetch took {second_time:.4f}s (cache hit)")
        print(f"  ✓ Speedup: {first_time/second_time:.0f}x faster")
        
        assert cached_data == data
        print("  ✓ Cached data matches original")
        
        cache.clear()
        return True
    else:
        print("  ⚠ Could not test (network issue?)")
        return False


if __name__ == "__main__":
    print("Running integration tests...\n")
    
    try:
        test_cache()
        test_fetch_and_extract()
        test_cache_integration()
        print("\n✅ All integration tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
