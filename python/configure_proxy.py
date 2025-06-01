#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Proxy Configuration Script for TMDB Scraper
Configures all modules to use Cloudflare Worker proxy to bypass errno 104 errors
"""

import sys
import os

# Add the lib directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

def configure_proxy(worker_url):
    """
    Configure all scraper modules to use the Cloudflare Worker proxy
    
    :param worker_url: Your Cloudflare Worker URL (e.g., 'https://your-worker.workers.dev')
    """
    try:
        from tmdbscraper import tmdbapi, fanarttv, api_utils
        
        print(f"Configuring proxy: {worker_url}")
        
        # Configure TMDB API proxy
        tmdbapi.set_proxy_base_url(worker_url)
        print("✓ TMDB API proxy configured")
        
        # Configure Fanart.tv proxy
        fanarttv.set_proxy_base_url(worker_url)
        print("✓ Fanart.tv proxy configured")
        
        print("✓ Proxy configuration complete!")
        print("\nAll API requests will now route through the Cloudflare Worker proxy.")
        
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Make sure you're running this from the python/ directory")
        return False
    
    return True

def disable_proxy():
    """
    Disable proxy and use direct API connections
    """
    try:
        from tmdbscraper import tmdbapi, fanarttv
        
        print("Disabling proxy configuration...")
        
        # Disable TMDB API proxy
        tmdbapi.set_proxy_base_url(None)
        print("✓ TMDB API proxy disabled")
        
        # Disable Fanart.tv proxy
        fanarttv.set_proxy_base_url(None)
        print("✓ Fanart.tv proxy disabled")
        
        print("✓ Direct API connections restored")
        
    except ImportError as e:
        print(f"Error importing modules: {e}")
        return False
    
    return True

def test_configuration():
    """
    Test the current configuration by making a test API call
    """
    try:
        from tmdbscraper import tmdbapi
        
        print("Testing TMDB API configuration...")
        config = tmdbapi.get_configuration()
        
        if 'error' in config:
            print(f"✗ API test failed: {config['error']}")
            return False
        else:
            print("✓ API test successful!")
            if 'images' in config:
                print(f"  Base URL: {config['images']['secure_base_url']}")
            return True
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("TMDB Scraper Proxy Configuration")
        print("=================================")
        print()
        print("Usage:")
        print("  python configure_proxy.py <worker_url>  - Configure proxy")
        print("  python configure_proxy.py disable       - Disable proxy")
        print("  python configure_proxy.py test          - Test current config")
        print()
        print("Example:")
        print("  python configure_proxy.py https://tmdb-scraper-proxy.your-subdomain.workers.dev")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "disable":
        disable_proxy()
    elif command == "test":
        test_configuration()
    elif command.startswith("http"):
        worker_url = command
        if configure_proxy(worker_url):
            print("\nTesting configuration...")
            test_configuration()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)