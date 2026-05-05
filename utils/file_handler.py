import os
import secrets
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
        
        # Create profiles folder
        base_path = os.path.join(current_app.root_path, 'static', 'uploads', 'profiles')
        os.makedirs(base_path, exist_ok=True)
        
        # Generate unique filename with timestamp
        import time
        filename = f"profile_{int(time.time())}_{secrets.token_hex(4)}.jpg"
        
        filepath = os.path.join(base_path, filename)
        file.save(filepath)
        
        print(f"✅ Saved to: {filepath}")
        return True, filename
    
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
        
        # Create resumes folder
        base_path = os.path.join(current_app.root_path, 'static', 'uploads', 'resumes')
        os.makedirs(base_path, exist_ok=True)
        
        # Generate unique filename with timestamp
        import time
        filename = f"resume_{int(time.time())}_{secrets.token_hex(4)}.pdf"
        
        filepath = os.path.join(base_path, filename)
        file.save(filepath)
        
        print(f"✅ Resume saved to: {filepath}")
        return True, filename
    
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
        
        # Create folder
        base_path = os.path.join(current_app.root_path, 'static', 'uploads', folder)
        os.makedirs(base_path, exist_ok=True)
        
        # Generate unique filename
        import time
        filename = f"{folder}_{int(time.time())}_{secrets.token_hex(4)}.jpg"
        
        filepath = os.path.join(base_path, filename)
        file.save(filepath)
        
        print(f"✅ Image saved to: {filepath}")
        return True, filename
    
    except Exception as e:
        print(f"❌ Save error: {str(e)}")
        return False, f'Error saving file: {str(e)}'

def delete_file(filename, folder='profiles'):
    """Delete a file from uploads folder"""
    try:
        if not filename or filename == 'default_profile.png':
            return False
        
        # Build path based on folder type
        base_path = os.path.join(current_app.root_path, 'static', 'uploads', folder)
        filepath = os.path.join(base_path, filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"✅ Deleted file: {filepath}")
            return True
        else:
            print(f"⚠️ File not found: {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Delete error: {str(e)}")
        return False

def delete_resume(filename):
    """Delete a resume file"""
    return delete_file(filename, 'resumes')