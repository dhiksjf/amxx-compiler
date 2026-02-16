import os
import uuid
import shutil
import base64
import subprocess
import re
import tempfile
import time
import zipfile
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from threading import Thread
import glob

app = Flask(__name__)

# Configuration
MAX_PLUGINS_PER_REQUEST = 10
MAX_INCLUDES_PER_REQUEST = 10
COMPILE_TIMEOUT = 30  # seconds per plugin
RATE_LIMIT_WINDOW = 120  # 120 seconds cooldown
CLEANUP_INTERVAL = 300  # Clean old files every 5 minutes
FILE_RETENTION_TIME = 600  # Keep files for 10 minutes

app.config['MAX_CONTENT_LENGTH'] = None  # Unlimited file size

# Rate limiting - 10 compilations per 120 seconds
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMPILER_PATH = os.path.join(BASE_DIR, "amxxpc")
OFFICIAL_INCLUDE_DIR = os.path.join(BASE_DIR, "scripting", "include")
TEMP_BASE_DIR = tempfile.gettempdir()
DOWNLOADS_DIR = os.path.join(TEMP_BASE_DIR, "amxx_downloads")

# Ensure downloads directory exists
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Store compilation metadata temporarily (no database)
compilation_metadata = {}

def cleanup_old_files():
    """Background thread to clean up old temporary files"""
    while True:
        try:
            current_time = time.time()
            
            # Clean download files
            for filename in os.listdir(DOWNLOADS_DIR):
                filepath = os.path.join(DOWNLOADS_DIR, filename)
                if os.path.isfile(filepath):
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > FILE_RETENTION_TIME:
                        os.remove(filepath)
            
            # Clean metadata
            expired_ids = [
                comp_id for comp_id, metadata in compilation_metadata.items()
                if current_time - metadata['timestamp'] > FILE_RETENTION_TIME
            ]
            for comp_id in expired_ids:
                del compilation_metadata[comp_id]
            
            # Clean temp directories
            for item in os.listdir(TEMP_BASE_DIR):
                if item.startswith('amxx_build_'):
                    dirpath = os.path.join(TEMP_BASE_DIR, item)
                    if os.path.isdir(dirpath):
                        try:
                            dir_age = current_time - os.path.getmtime(dirpath)
                            if dir_age > FILE_RETENTION_TIME:
                                shutil.rmtree(dirpath, ignore_errors=True)
                        except:
                            pass
            
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        time.sleep(CLEANUP_INTERVAL)

# Start cleanup thread
cleanup_thread = Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

def parse_compiler_output(output):
    """Parse compiler output for errors and warnings"""
    errors, warnings = [], []
    err_pattern = re.compile(r'.*?\((\d+)\)\s+:\s+error\s+(\d+):\s+(.*)')
    warn_pattern = re.compile(r'.*?\((\d+)\)\s+:\s+warning\s+(\d+):\s+(.*)')

    for line in output.splitlines():
        if match := err_pattern.match(line):
            errors.append({
                "line": int(match.group(1)),
                "code": int(match.group(2)),
                "message": match.group(3).strip()
            })
        elif match := warn_pattern.match(line):
            warnings.append({
                "line": int(match.group(1)),
                "code": int(match.group(2)),
                "message": match.group(3).strip()
            })
    return errors, warnings

def validate_filename(filename):
    """Validate filename security"""
    return (filename and 
            re.match(r'^[a-zA-Z0-9_\-\.]+$', filename) and 
            '..' not in filename and 
            '/' not in filename and 
            '\\' not in filename)

def create_zip_file(compiled_files, compilation_id):
    """Create a ZIP file containing all compiled plugins"""
    zip_filename = f"compiled_plugins_{compilation_id}.zip"
    zip_path = os.path.join(DOWNLOADS_DIR, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for plugin_name, amxx_data in compiled_files:
            # Write the .amxx file to zip
            zipf.writestr(f"{plugin_name}.amxx", amxx_data)
    
    return zip_filename

@app.route("/", methods=["GET"])
def serve_interface():
    """Serve the web interface"""
    return send_file('index.html')

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "AMXX Compiler API",
        "version": "2.0.0",
        "features": [
            "Compile up to 10 .sma files per request",
            "Support for 10 custom .inc files per request",
            "Unlimited file sizes",
            "120 second rate limit (10 compilations per 120s)",
            "Automatic file cleanup",
            "ZIP download for compiled plugins"
        ],
        "endpoints": {
            "compile": "/compile (POST)",
            "download": "/download/<compilation_id> (GET)",
            "stats": "/stats (GET)"
        },
        "limits": {
            "max_plugins": MAX_PLUGINS_PER_REQUEST,
            "max_includes": MAX_INCLUDES_PER_REQUEST,
            "rate_limit": f"{MAX_PLUGINS_PER_REQUEST} compilations per {RATE_LIMIT_WINDOW} seconds",
            "timeout_per_plugin": f"{COMPILE_TIMEOUT} seconds"
        }
    }), 200

@app.route("/stats", methods=["GET"])
def get_stats():
    """Get compilation statistics"""
    active_compilations = len(compilation_metadata)
    total_files = len(os.listdir(DOWNLOADS_DIR))
    
    return jsonify({
        "active_compilations": active_compilations,
        "available_downloads": total_files,
        "cleanup_interval": f"{CLEANUP_INTERVAL} seconds",
        "file_retention": f"{FILE_RETENTION_TIME} seconds"
    }), 200

@app.route("/compile", methods=["POST"])
@limiter.limit(f"{MAX_PLUGINS_PER_REQUEST} per {RATE_LIMIT_WINDOW} seconds")
def compile_plugins():
    """
    Main compilation endpoint
    
    Accepts JSON with:
    {
        "includes": {"file.inc": "content"},  // Optional, max 10 files
        "plugins": [                          // Required, max 10 plugins
            {
                "name": "plugin_name",
                "code": "// AMX Mod X source code",
                "includes": {"custom.inc": "content"}  // Optional per plugin
            }
        ]
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        # Validate input
        shared_includes = data.get("includes", {})
        plugins = data.get("plugins", [])
        
        if not isinstance(plugins, list):
            return jsonify({"error": "Plugins must be a list"}), 400
        
        if len(plugins) == 0:
            return jsonify({"error": "At least one plugin is required"}), 400
        
        if len(plugins) > MAX_PLUGINS_PER_REQUEST:
            return jsonify({
                "error": f"Maximum {MAX_PLUGINS_PER_REQUEST} plugins per request",
                "your_request": len(plugins),
                "wait_time": f"{RATE_LIMIT_WINDOW} seconds"
            }), 400
        
        if len(shared_includes) > MAX_INCLUDES_PER_REQUEST:
            return jsonify({
                "error": f"Maximum {MAX_INCLUDES_PER_REQUEST} shared includes per request",
                "your_request": len(shared_includes)
            }), 400

        # Create unique compilation ID
        compilation_id = str(uuid.uuid4())
        request_dir = os.path.join(TEMP_BASE_DIR, f"amxx_build_{compilation_id}")
        os.makedirs(request_dir, exist_ok=True)
        
        results = []
        compiled_files = []  # Store successful compilations for ZIP
        total_success = 0
        total_failed = 0

        # Process shared includes
        shared_inc_dir = os.path.join(request_dir, "shared_include")
        os.makedirs(shared_inc_dir, exist_ok=True)
        
        for inc_name, inc_content in shared_includes.items():
            if validate_filename(inc_name) and inc_name.endswith(".inc"):
                with open(os.path.join(shared_inc_dir, inc_name), "w", encoding="utf-8", errors='ignore') as f:
                    f.write(inc_content)

        # Process each plugin
        for idx, plugin in enumerate(plugins):
            plugin_name = plugin.get("name", f"plugin_{idx+1}")
            plugin_code = plugin.get("code", "")
            plugin_includes = plugin.get("includes", {})

            # Sanitize plugin name
            if not validate_filename(plugin_name):
                plugin_name = f"plugin_{idx+1}"

            # Create build directory for this plugin
            build_dir = os.path.join(request_dir, f"build_{idx}")
            os.makedirs(build_dir, exist_ok=True)

            # Process plugin-specific includes
            custom_inc_dir = os.path.join(build_dir, "include")
            os.makedirs(custom_inc_dir, exist_ok=True)
            
            for inc_name, inc_content in plugin_includes.items():
                if validate_filename(inc_name) and inc_name.endswith(".inc"):
                    with open(os.path.join(custom_inc_dir, inc_name), "w", encoding="utf-8", errors='ignore') as f:
                        f.write(inc_content)

            # Write source file
            sma_filename = secure_filename(plugin_name) + ".sma"
            amxx_filename = secure_filename(plugin_name) + ".amxx"
            sma_path = os.path.join(build_dir, sma_filename)
            amxx_path = os.path.join(build_dir, amxx_filename)
            
            with open(sma_path, "w", encoding="utf-8", errors='ignore') as f:
                f.write(plugin_code)

            # Compile
            cmd = [
                COMPILER_PATH,
                sma_filename,
                f"-o{amxx_filename}",
                f"-i{OFFICIAL_INCLUDE_DIR}",
                f"-i{shared_inc_dir}",
                f"-i{custom_inc_dir}"
            ]
            
            try:
                process = subprocess.run(
                    cmd,
                    cwd=build_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=COMPILE_TIMEOUT,
                    env={"LD_LIBRARY_PATH": BASE_DIR}
                )
                
                log = process.stdout
                success = process.returncode == 0 and os.path.exists(amxx_path)
                
                if success:
                    # Read compiled file
                    with open(amxx_path, "rb") as f:
                        amxx_data = f.read()
                    
                    compiled_files.append((plugin_name, amxx_data))
                    total_success += 1
                else:
                    total_failed += 1
                
                errors, warnings = parse_compiler_output(log)
                
                results.append({
                    "plugin": plugin_name,
                    "success": success,
                    "errors": errors,
                    "warnings": warnings,
                    "log": log,
                    "size": len(amxx_data) if success else 0
                })
                
            except subprocess.TimeoutExpired:
                results.append({
                    "plugin": plugin_name,
                    "success": False,
                    "errors": [{"line": 0, "code": 0, "message": f"Compilation timed out after {COMPILE_TIMEOUT} seconds"}],
                    "warnings": [],
                    "log": f"Timeout after {COMPILE_TIMEOUT} seconds",
                    "size": 0
                })
                total_failed += 1
                
            except Exception as e:
                results.append({
                    "plugin": plugin_name,
                    "success": False,
                    "errors": [{"line": 0, "code": 0, "message": str(e)}],
                    "warnings": [],
                    "log": str(e),
                    "size": 0
                })
                total_failed += 1

        # Create ZIP file if any compilation succeeded
        download_url = None
        zip_size = 0
        
        if compiled_files:
            zip_filename = create_zip_file(compiled_files, compilation_id)
            zip_path = os.path.join(DOWNLOADS_DIR, zip_filename)
            zip_size = os.path.getsize(zip_path)
            
            # Store metadata
            compilation_metadata[compilation_id] = {
                'timestamp': time.time(),
                'zip_filename': zip_filename,
                'total_plugins': len(plugins),
                'successful': total_success,
                'failed': total_failed
            }
            
            # Generate download URL
            download_url = f"/download/{compilation_id}"

        # Cleanup build directory
        shutil.rmtree(request_dir, ignore_errors=True)

        # Build response
        response = {
            "compilation_id": compilation_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "summary": {
                "total_plugins": len(plugins),
                "successful": total_success,
                "failed": total_failed,
                "success_rate": f"{(total_success/len(plugins)*100):.1f}%"
            },
            "results": results,
            "download": {
                "available": download_url is not None,
                "url": download_url,
                "filename": compilation_metadata.get(compilation_id, {}).get('zip_filename'),
                "size_bytes": zip_size,
                "size_mb": f"{zip_size / 1024 / 1024:.2f}",
                "expires_in": f"{FILE_RETENTION_TIME} seconds"
            } if download_url else None,
            "rate_limit_info": {
                "next_available": f"in {RATE_LIMIT_WINDOW} seconds",
                "max_per_window": MAX_PLUGINS_PER_REQUEST
            }
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500

@app.route("/download/<compilation_id>", methods=["GET"])
def download_compiled(compilation_id):
    """Download compiled plugins as ZIP file"""
    try:
        # Check if compilation exists
        if compilation_id not in compilation_metadata:
            return jsonify({
                "error": "Compilation not found",
                "message": "The compilation ID is invalid or has expired",
                "retention_time": f"{FILE_RETENTION_TIME} seconds"
            }), 404
        
        metadata = compilation_metadata[compilation_id]
        zip_filename = metadata['zip_filename']
        zip_path = os.path.join(DOWNLOADS_DIR, zip_filename)
        
        # Check if file exists
        if not os.path.exists(zip_path):
            return jsonify({
                "error": "File not found",
                "message": "The compiled files have been cleaned up"
            }), 404
        
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
        
    except Exception as e:
        return jsonify({
            "error": "Download failed",
            "message": str(e)
        }), 500

@app.route("/info/<compilation_id>", methods=["GET"])
def get_compilation_info(compilation_id):
    """Get information about a compilation"""
    if compilation_id not in compilation_metadata:
        return jsonify({
            "error": "Compilation not found",
            "message": "The compilation ID is invalid or has expired"
        }), 404
    
    metadata = compilation_metadata[compilation_id]
    current_time = time.time()
    age = current_time - metadata['timestamp']
    remaining = FILE_RETENTION_TIME - age
    
    return jsonify({
        "compilation_id": compilation_id,
        "created": datetime.fromtimestamp(metadata['timestamp']).isoformat() + "Z",
        "age_seconds": int(age),
        "expires_in_seconds": int(max(0, remaining)),
        "summary": {
            "total_plugins": metadata['total_plugins'],
            "successful": metadata['successful'],
            "failed": metadata['failed']
        },
        "download": {
            "filename": metadata['zip_filename'],
            "url": f"/download/{compilation_id}"
        }
    }), 200

@app.errorhandler(429)
def ratelimit_handler(e):
    """Custom rate limit error handler"""
    return jsonify({
        "error": "Rate limit exceeded",
        "message": f"You have reached the maximum of {MAX_PLUGINS_PER_REQUEST} compilations per {RATE_LIMIT_WINDOW} seconds",
        "retry_after": f"{RATE_LIMIT_WINDOW} seconds",
        "tip": "Please wait before making another compilation request"
    }), 429

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
