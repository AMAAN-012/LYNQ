from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db
from models.user import User
from models.skill import Skill
from models.post import Post
from models.comment import Comment
from models.application import Application
from models.job import Job
from utils.file_handler import save_profile_picture, save_image, delete_file

# ✅ DEFINE BLUEPRINT FIRST
user_bp = Blueprint('user', __name__, url_prefix='/profile')

def check_user_session():
    """Check if user session is valid"""
    if 'user_id' not in session:
        return None
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Your session has expired. Please login again.', 'error')
        return None
    
    return user

@user_bp.route('/')
def profile():
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    stats = user.get_stats()
    skills = Skill.query.filter_by(user_id=user.id).all()
    recent_posts = Post.query.filter_by(author_id=user.id).order_by(Post.created_at.desc()).limit(5).all()

    if user.is_admin:
        recent_jobs = Job.query.filter_by(company_id=user.id).order_by(Job.created_at.desc()).limit(5).all()
        recent_applications = []
    else:
        recent_applications = (
            Application.query
            .filter_by(user_id=user.id)
            .order_by(Application.applied_at.desc())
            .limit(5).all()
        )
        recent_jobs = []

    return render_template(
        'user/profile.html',
        user=user,
        stats=stats,
        skills=skills,
        recent_posts=recent_posts,
        recent_jobs=recent_jobs,
        recent_applications=recent_applications,
    )

@user_bp.route('/edit', methods=['GET', 'POST'])
def edit_profile():
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        bio = request.form.get('bio', '').strip()
        age = request.form.get('age', '').strip()
        company_name = request.form.get('company_name', '').strip()
        cgpa = request.form.get('cgpa', '').strip()
        
        if not full_name:
            flash('Full name cannot be empty', 'error')
            return redirect(url_for('user.edit_profile'))
        
        user.full_name = full_name
        user.bio = bio if bio else None
        user.age = int(age) if age else None
        user.company_name = company_name if company_name else None
        
        if not user.is_admin and cgpa:
            try:
                user.cgpa = float(cgpa)
            except ValueError:
                flash('CGPA must be a valid number', 'error')
                return redirect(url_for('user.edit_profile'))
        
        # Handle profile picture upload
        if 'profile_picture_file' in request.files:
            profile_file = request.files['profile_picture_file']
            if profile_file and profile_file.filename:
                try:
                    # Delete old profile picture
                    if user.profile_picture and user.profile_picture != 'default_profile.png':
                        delete_file(user.profile_picture, 'profiles')
                        print(f"✅ Deleted old picture: {user.profile_picture}")
                    
                    # Save new picture
                    success, result = save_profile_picture(profile_file)
                    if success:
                        user.profile_picture = result
                        print(f"✅ New picture saved: {result}")
                        db.session.commit()
                        flash('Profile updated successfully!', 'success')
                    else:
                        flash(f'Error saving picture: {result}', 'error')
                        return redirect(url_for('user.edit_profile'))
                        
                except Exception as e:
                    print(f"❌ Error: {str(e)}")
                    flash(f'Error processing profile picture: {str(e)}', 'error')
                    return redirect(url_for('user.edit_profile'))
            else:
                # No image uploaded, just update other fields
                db.session.commit()
                flash('Profile updated successfully!', 'success')
        else:
            # No image uploaded, just update other fields
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        
        session['full_name'] = full_name
        return redirect(url_for('user.profile'))
    
    return render_template('user/edit_profile.html', user=user)
    

@user_bp.route('/skill/add', methods=['GET', 'POST'])
def add_skill():
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        certification = request.form.get('certification', '').strip()
        verification_link = request.form.get('verification_link', '').strip()
        
        if not name:
            flash('Skill name cannot be empty', 'error')
            return redirect(url_for('user.add_skill'))
        
        certificate_file = None
        if 'certificate' in request.files:
            cert_file = request.files['certificate']
            if cert_file and cert_file.filename:
                success, result = save_image(cert_file, 'certificates')
                if success:
                    certificate_file = result
                else:
                    flash(f'Certificate upload error: {result}', 'error')
                    return redirect(url_for('user.add_skill'))
        
        skill = Skill(
            name=name,
            certification=certification if certification else None,
            verification_link=verification_link if verification_link else None,
            certificate_file=certificate_file,
            user_id=user.id
        )
        db.session.add(skill)
        db.session.commit()
        
        flash('Skill added successfully!', 'success')
        return redirect(url_for('user.profile'))
    
    return render_template('user/add_skill.html', user=user)

@user_bp.route('/skill/<int:skill_id>/edit', methods=['GET', 'POST'])
def edit_skill(skill_id):
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    skill = Skill.query.get_or_404(skill_id)
    
    if skill.user_id != user.id:
        flash('You can only edit your own skills', 'error')
        return redirect(url_for('user.profile'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        certification = request.form.get('certification', '').strip()
        verification_link = request.form.get('verification_link', '').strip()
        
        if not name:
            flash('Skill name cannot be empty', 'error')
            return redirect(url_for('user.edit_skill', skill_id=skill_id))
        
        skill.name = name
        skill.certification = certification if certification else None
        skill.verification_link = verification_link if verification_link else None
        
        # Handle certificate upload
        if 'certificate' in request.files:
            cert_file = request.files['certificate']
            if cert_file and cert_file.filename:
                # Delete old certificate if exists
                if skill.certificate_file:
                    delete_file(skill.certificate_file, 'certificates')
                
                success, result = save_image(cert_file, 'certificates')
                if success:
                    skill.certificate_file = result
                else:
                    flash(f'Certificate upload error: {result}', 'error')
                    return redirect(url_for('user.edit_skill', skill_id=skill_id))
        
        db.session.commit()
        
        flash('Skill updated successfully!', 'success')
        return redirect(url_for('user.profile'))
    
    return render_template('user/edit_skill.html', skill=skill, user=user)

@user_bp.route('/skill/<int:skill_id>/delete', methods=['POST'])
def delete_skill(skill_id):
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    skill = Skill.query.get_or_404(skill_id)
    
    if skill.user_id != user.id:
        flash('You can only delete your own skills', 'error')
        return redirect(url_for('user.profile'))
    
    try:
        # Delete certificate file if exists
        if skill.certificate_file:
            delete_file(skill.certificate_file, 'certificates')
        
        db.session.delete(skill)
        db.session.commit()
        flash('Skill deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting skill: {str(e)}', 'error')
    
    return redirect(url_for('user.profile'))