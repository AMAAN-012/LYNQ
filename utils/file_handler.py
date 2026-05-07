import os
import secrets
import cloudinary.uploader
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {
    'profile': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'},
    'resume': {'pdf', 'doc', 'docx'},
    'certificates': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'},
    'certificate': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
}

def allowed_file(filename, file_type='resume'):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS.get(file_type, set())


def save_profile_picture(file):
    """Save profile picture with unique filename"""
    try:
        if not file or file.filename == '':
            return False, 'No file selected'
        
        if not allowed_file(file.filename, 'profile'):
            return False, 'Only PNG, JPG, JPEG, GIF, WebP files allowed'
        
        # 🔥 NEW: Upload to Cloudinary
        result = cloudinary.uploader.upload(file, folder="profiles")
        image_url = result['secure_url']
        
        print(f"✅ Uploaded to Cloudinary: {image_url}")
        return True, image_url
    
    except Exception as e:
        print(f"❌ Save error: {str(e)}")
        return False, f'Error saving file: {str(e)}'


def save_resume(file):
    """Save resume/CV file with unique filename"""
    try:
        if not file or file.filename == '':
            return False, 'No file selected'
        
        if not allowed_file(file.filename, 'resume'):
            return False, 'Only PDF, DOC, DOCX files allowed'
        
        # 🔥 NEW: Upload to Cloudinary (raw for pdf/doc)
        result = cloudinary.uploader.upload(
            file,
            folder="resumes",
            resource_type="raw"
        )
        file_url = result['secure_url']
        
        print(f"✅ Resume uploaded: {file_url}")
        return True, file_url
    
    except Exception as e:
        print(f"❌ Resume save error: {str(e)}")
        return False, f'Error saving file: {str(e)}'


def save_image(file, folder='certificates'):
    """Save image file (for certificates, etc)"""
    try:
        if not file or file.filename == '':
            return False, 'No file selected'
        
        # Check file extension
        if '.' not in file.filename:
            return False, 'File must have an extension'
        
        ext = file.filename.rsplit('.', 1)[1].lower()
        
        # Allow image extensions
        allowed_exts = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'}
        
        if ext not in allowed_exts:
            return False, f'Only image files allowed (.png, .jpg, .jpeg, .gif, .webp)'
        
        # 🔥 NEW: Upload to Cloudinary
        result = cloudinary.uploader.upload(file, folder=folder)
        image_url = result['secure_url']
        
        print(f"✅ Image uploaded: {image_url}")
        return True, image_url
    
    except Exception as e:
        print(f"❌ Save error: {str(e)}")
        return False, f'Error saving file: {str(e)}'


def delete_file(filename, folder='profiles'):
    """Delete a file (Cloudinary version skip for now)"""
    return True


def delete_resume(filename):
    """Delete a resume file"""
    return True




