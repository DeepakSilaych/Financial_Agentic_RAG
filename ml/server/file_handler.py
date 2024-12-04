from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
import os
import logging
import shutil
from typing import List, Dict
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_DIR = "data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_space_dir(space_id: int) -> str:
    """Get the directory for a space, creating it if it doesn't exist"""
    space_dir = os.path.join(UPLOAD_DIR, str(space_id))
    os.makedirs(space_dir, exist_ok=True)
    return space_dir

def get_absolute_path(space_id: int, path: str) -> str:
    """Convert a relative path to absolute path within a space"""
    space_dir = get_space_dir(space_id)
    if path == "" or path == "/":
        return space_dir
    # Clean the path to prevent directory traversal
    safe_path = os.path.normpath(path).lstrip('/')
    return os.path.join(space_dir, safe_path)

def list_items(space_id: int, path: str) -> List[Dict]:
    """List all items (files and folders) in the specified path"""
    try:
        # If path contains 'download', ignore it and just use the space directory
        if 'download' in path:
            target_dir = get_space_dir(space_id)
        else:
            target_dir = get_absolute_path(space_id, path)
            
        logger.info(f"Listing items in directory: {target_dir}")
        
        if not os.path.exists(target_dir):
            logger.warning(f"Directory does not exist: {target_dir}")
            return []

        items = []
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            stats = os.stat(item_path)
            
            base_info = {
                "name": item,
                "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                "lastModified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "owner": "Current User"
            }
            
            if os.path.isfile(item_path):
                file_ext = os.path.splitext(item)[1][1:].lower()
                file_type = get_file_type(item)
                items.append({
                    **base_info,
                    "size": stats.st_size,
                    "tag": file_ext,
                    "type": file_type,
                    "url": get_file_url(space_id, item)
                })
            else:
                items.append({
                    **base_info,
                    "type": "folder"
                })
        
        logger.info(f"Found {len(items)} items in directory")
        return sorted(items, key=lambda x: (x["type"] == "file", x["name"].lower()))
    except Exception as e:
        logger.error(f"Error listing items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_file_type(filename: str) -> str:
    """Get the type of file based on its extension"""
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    if ext in ['pdf']:
        return 'pdf'
    elif ext in ['jpg', 'jpeg', 'png', 'gif']:
        return 'image'
    elif ext in ['mp4', 'avi', 'mov']:
        return 'video'
    elif ext in ['mp3', 'wav']:
        return 'audio'
    else:
        return 'file'

def get_file_url(space_id: int, filename: str) -> str:
    """Get the URL for accessing a file through the data endpoint"""
    return f"/data/{space_id}/{filename}"

async def save_upload_file(file: UploadFile, space_id: int, path: str) -> Dict:
    """Save an uploaded file to the specified path"""
    try:
        space_dir = get_space_dir(space_id)
        # Store files directly in the space directory
        file_path = os.path.join(space_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_stat = os.stat(file_path)
        
        return {
            "name": file.filename,
            "size": file_stat.st_size,
            "type": get_file_type(file.filename),
            "url": get_file_url(space_id, file.filename),  # URL without additional path
            "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
        }
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def create_folder(space_id: int, path: str, name: str) -> Dict:
    """Create a new folder at the specified path"""
    try:
        parent_dir = get_absolute_path(space_id, path)
        folder_path = os.path.join(parent_dir, name)
        
        if os.path.exists(folder_path):
            raise HTTPException(status_code=400, detail="Folder already exists")
            
        os.makedirs(folder_path, exist_ok=True)
        stats = os.stat(folder_path)
        
        return {
            "name": name,
            "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "lastModified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "owner": "Current User",
            "type": "folder"
        }
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def delete_item(space_id: int, path: str, name: str) -> bool:
    """Delete a file or folder at the specified path"""
    try:
        parent_dir = get_absolute_path(space_id, path)
        item_path = os.path.join(parent_dir, name)
        
        if not os.path.exists(item_path):
            raise HTTPException(status_code=404, detail="Item not found")
        
        if os.path.isfile(item_path):
            os.remove(item_path)
        else:
            shutil.rmtree(item_path)
        
        return True
    except Exception as e:
        logger.error(f"Error deleting item: {e}")
        return False

def get_file(space_id: int, path: str, filename: str) -> FileResponse:
    """Get a file at the specified path"""
    try:
        # If path is empty, look for the file directly in the space directory
        if not path or path == "/":
            file_path = os.path.join(get_space_dir(space_id), filename)
        else:
            target_dir = get_absolute_path(space_id, path)
            file_path = os.path.join(target_dir, filename)
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file extension and set appropriate content type
        file_ext = os.path.splitext(filename)[1][1:].lower()
        content_type = None
        
        if file_ext == 'pdf':
            content_type = 'application/pdf'
        elif file_ext in ['jpg', 'jpeg']:
            content_type = 'image/jpeg'
        elif file_ext == 'png':
            content_type = 'image/png'
        elif file_ext == 'gif':
            content_type = 'image/gif'
        else:
            content_type = 'application/octet-stream'
        
        logger.info(f"Serving file: {file_path} with content type: {content_type}")
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": content_type
            }
        )
    except Exception as e:
        logger.error(f"Error getting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
