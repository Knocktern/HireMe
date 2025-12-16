import subprocess
import tempfile
import uuid
import requests

# Online execution configuration
ONLINE_EXECUTION_ENABLED = True
PISTON_API_URL = "https://emkc.org/api/v2/piston"

PISTON_LANGUAGE_MAP = {
    'javascript': {'language': 'javascript', 'version': '*'},
    'python': {'language': 'python', 'version': '*'},
    'java': {'language': 'java', 'version': '*'},
    'cpp': {'language': 'cpp', 'version': '*'},
    'c': {'language': 'c', 'version': '*'},
    'csharp': {'language': 'csharp', 'version': '*'},
    'php': {'language': 'php', 'version': '*'},
    'ruby': {'language': 'ruby', 'version': '*'},
    'rust': {'language': 'rust', 'version': '*'},
    'swift': {'language': 'swift', 'version': '*'},
}

def execute_code_online(code, language):
    """Execute code using the Piston API"""
    try:
        if not ONLINE_EXECUTION_ENABLED:
            return "Online code execution is disabled."
            
        language_info = PISTON_LANGUAGE_MAP.get(language)
        if not language_info:
            return f"Language '{language}' is not supported."
            
        # Get available runtimes
        runtimes_response = requests.get(f"{PISTON_API_URL}/runtimes")
        if runtimes_response.status_code != 200:
            return "API Error: Failed to get available runtimes"
            
        runtimes = runtimes_response.json()
        
        # Find the latest version
        lang_name = language_info['language']
        version = None
        for runtime in runtimes:
            if runtime['language'] == lang_name:
                version = runtime['version']
                break
                
        if not version:
            return f"Language '{language}' is not available."
            
        # Execute code
        payload = {
            "language": lang_name,
            "version": version,
            "files": [{"content": code}],
            "stdin": "",
            "args": [],
            "compile_timeout": 10000,
            "run_timeout": 3000,
            "compile_memory_limit": -1,
            "run_memory_limit": -1
        }
        
        response = requests.post(f"{PISTON_API_URL}/execute", json=payload)
        if response.status_code != 200:
            return f"API Error: {response.text}"
            
        result = response.json()
        
        # Check for compilation errors
        if 'compile' in result and result['compile']['code'] != 0:
            return f"Compilation Error: {result['compile']['stderr']}"
            
        # Get run results
        run_result = result.get('run', {})
        stdout = run_result.get('stdout', '')
        stderr = run_result.get('stderr', '')
        exit_code = run_result.get('code', 0)
        
        if exit_code == 0:
            return stdout
        else:
            return f"Execution Error (code {exit_code}): {stderr}"
            
    except Exception as e:
        return f"Online execution error: {str(e)}"

def execute_code(code, language):
    """Execute code via online Piston API only."""
    return execute_code_online(code, language)
