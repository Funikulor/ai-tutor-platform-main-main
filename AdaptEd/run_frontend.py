#!/usr/bin/env python3
"""
Simple script to run the AdaptEd frontend.
"""
import sys
import os

# Add the frontend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend'))

if __name__ == "__main__":
    os.chdir('frontend')
    import streamlit.web.cli as stcli
    
    print("Starting AdaptEd Frontend...")
    print("Frontend will be available at: http://localhost:8501")
    print("\nPress Ctrl+C to stop the server.\n")
    
    sys.argv = ["streamlit", "run", "app.py"]
    sys.exit(stcli.main())
