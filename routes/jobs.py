from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from models import db
from models.job import Job
from models.application import Application
from models.user import User
from utils.file_handler import allowed_file, save_resume, delete_resume
import os

jobs_bp = Blueprint('jobs', __name__, url_prefix='/jobs')

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

@jobs_bp.route('/')
def list_jobs():
    """List all available jobs"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    jobs = Job.query.all()
    return render_template('jobs/jobs_list.html', jobs=jobs, user=user)

@jobs_bp.route('/my-applications')
def my_applications():
    """View user's applications (USERS ONLY)"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    # Admin users don't apply for jobs
    if user.is_admin:
        flash('Admin users cannot view applications', 'error')
        return redirect(url_for('jobs.list_jobs'))
    
    # Get all applications for this user
    applications = Application.query.filter_by(user_id=user.id).order_by(Application.applied_at.desc()).all()
    
    return render_template('jobs/my_applications.html', applications=applications, user=user)

@jobs_bp.route('/application/<int:app_id>')
def view_application_detail(app_id):
    """View application detail (USER can view own, ADMIN can view any)"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    application = Application.query.get_or_404(app_id)
    
    # Check authorization
    if application.user_id != user.id and not user.is_admin:
        flash('You can only view your own applications', 'error')
        return redirect(url_for('jobs.my_applications'))
    
    return render_template('jobs/application_detail.html', application=application, user=user)

@jobs_bp.route('/create', methods=['GET', 'POST'])
def create_job():
    """Create a new job (ADMIN ONLY)"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    if not user.is_admin:
        flash('Only admins can create jobs', 'error')
        return redirect(url_for('jobs.list_jobs'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        # FIX: Removed 'company' from form (it's stored as company_id in the admin user record)
        if not title or not description:
            flash('Title and description are required', 'error')
            return redirect(url_for('jobs.create_job'))
        
        try:
            # FIX: Only pass company_id (not company string)
            job = Job(
                title=title,
                description=description,
                company_id=user.id,  # FIX: Use company_id, not company
                salary_range=request.form.get('salary_range', '').strip(),
                location=request.form.get('location', '').strip(),
                job_type=request.form.get('job_type', '').strip(),
                requirements=request.form.get('requirements', '').strip()
            )
            db.session.add(job)
            db.session.commit()
            
            # FIX: Refresh user to update stats
            db.session.refresh(user)
            
            flash('Job created successfully!', 'success')
            return redirect(url_for('jobs.list_jobs'))
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating job: {str(e)}")
            flash(f'Error creating job: {str(e)}', 'error')
            return redirect(url_for('jobs.create_job'))
    
    return render_template('jobs/create_job.html', user=user)

@jobs_bp.route('/<int:job_id>/apply', methods=['POST'])
def apply_job(job_id):
    """Apply for a job (USERS ONLY - NOT ADMINS)"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    # Admin users cannot apply for jobs
    if user.is_admin:
        flash('Admin users cannot apply for jobs', 'error')
        return redirect(url_for('jobs.list_jobs'))
    
    job = Job.query.get_or_404(job_id)
    
    # Check if already applied
    existing = Application.query.filter_by(
        job_id=job_id,
        user_id=user.id
    ).first()
    
    if existing:
        flash('You have already applied for this job', 'error')
        return redirect(url_for('jobs.list_jobs'))
    
    try:
        # Get form data
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        linkedin_url = request.form.get('linkedin_url', '').strip()
        portfolio_url = request.form.get('portfolio_url', '').strip()
        cover_letter = request.form.get('cover_letter', '').strip()
        
        # Validate required fields
        if not phone:
            flash('Phone number is required', 'error')
            return redirect(url_for('jobs.list_jobs'))
        
        if not email:
            flash('Email is required', 'error')
            return redirect(url_for('jobs.list_jobs'))
        
        # Handle resume upload
        resume_filename = None
        if 'resume' in request.files:
            resume_file = request.files['resume']
            if resume_file and resume_file.filename:
                success, result = save_resume(resume_file)
                if success:
                    resume_filename = result
                else:
                    flash(f'Resume upload error: {result}', 'error')
                    return redirect(url_for('jobs.list_jobs'))
        
        # Create application
        application = Application(
            job_id=job_id,
            user_id=user.id,
            phone=phone,
            email=email,
            linkedin_url=linkedin_url if linkedin_url else None,
            portfolio_url=portfolio_url if portfolio_url else None,
            cover_letter=cover_letter if cover_letter else None,
            resume_filename=resume_filename
        )
        db.session.add(application)
        db.session.commit()
        
        # FIX: Refresh user to update stats
        db.session.refresh(user)
        
        flash('Application submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error submitting application: {str(e)}")
        flash(f'Error submitting application: {str(e)}', 'error')
    
    return redirect(url_for('jobs.list_jobs'))

@jobs_bp.route('/<int:job_id>/edit', methods=['GET', 'POST'])
def edit_job(job_id):
    """Edit a job (ADMIN ONLY)"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    if not user.is_admin:
        flash('Only admins can edit jobs', 'error')
        return redirect(url_for('jobs.list_jobs'))
    
    job = Job.query.get_or_404(job_id)
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        # FIX: Removed 'company' from validation
        if not title or not description:
            flash('Title and description are required', 'error')
            return redirect(url_for('jobs.edit_job', job_id=job_id))
        
        try:
            job.title = title
            job.description = description
            job.salary_range = request.form.get('salary_range', '').strip()
            job.location = request.form.get('location', '').strip()
            job.job_type = request.form.get('job_type', '').strip()
            job.requirements = request.form.get('requirements', '').strip()
            
            db.session.commit()
            
            # FIX: Refresh user to update stats
            db.session.refresh(user)
            
            flash('Job updated successfully!', 'success')
            return redirect(url_for('jobs.list_jobs'))
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating job: {str(e)}")
            flash(f'Error updating job: {str(e)}', 'error')
            return redirect(url_for('jobs.edit_job', job_id=job_id))
    
    return render_template('jobs/edit_job.html', job=job, user=user)

@jobs_bp.route('/<int:job_id>/delete', methods=['POST'])
def delete_job(job_id):
    """Delete a job (ADMIN ONLY)"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    if not user.is_admin:
        flash('Only admins can delete jobs', 'error')
        return redirect(url_for('jobs.list_jobs'))
    
    job = Job.query.get_or_404(job_id)
    
    try:
        db.session.delete(job)
        db.session.commit()
        
        # FIX: Refresh user to update stats
        db.session.refresh(user)
        
        flash('Job deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error deleting job: {str(e)}")
        flash(f'Error deleting job: {str(e)}', 'error')
    
    return redirect(url_for('jobs.list_jobs'))

@jobs_bp.route('/<int:job_id>/applications')
def job_applications(job_id):
    """View applications for a job (ADMIN ONLY)"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    if not user.is_admin:
        flash('Only admins can view applications', 'error')
        return redirect(url_for('jobs.list_jobs'))
    
    job = Job.query.get_or_404(job_id)
    applications = Application.query.filter_by(job_id=job_id).order_by(Application.applied_at.desc()).all()
    
    return render_template('jobs/job_applications.html', job=job, applications=applications, user=user)

@jobs_bp.route('/application/<int:app_id>/resume')
def download_resume(app_id):
    """Download applicant's resume (ADMIN ONLY)"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    if not user.is_admin:
        flash('Only admins can download resumes', 'error')
        return redirect(url_for('jobs.list_jobs'))
    
    application = Application.query.get_or_404(app_id)
    
    if not application.resume_filename:
        flash('No resume uploaded for this application', 'error')
        return redirect(url_for('jobs.job_applications', job_id=application.job_id))
    
    try:
        from flask import current_app
        resume_path = os.path.join(current_app.config['UPLOAD_FOLDER'], application.resume_filename)
        
        if not os.path.exists(resume_path):
            flash('Resume file not found', 'error')
            return redirect(url_for('jobs.job_applications', job_id=application.job_id))
        
        return send_file(resume_path, as_attachment=True)
    except Exception as e:
        print(f"❌ Error downloading resume: {str(e)}")
        flash(f'Error downloading resume: {str(e)}', 'error')
        return redirect(url_for('jobs.job_applications', job_id=application.job_id))

@jobs_bp.route('/application/<int:app_id>/status', methods=['POST'])
def update_application_status(app_id):
    """Update application status (ADMIN ONLY)"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    if not user.is_admin:
        flash('Only admins can update application status', 'error')
        return redirect(url_for('jobs.list_jobs'))
    
    application = Application.query.get_or_404(app_id)
    status = request.form.get('status', '').strip()
    review_notes = request.form.get('review_notes', '').strip()
    
    if status not in ['pending', 'reviewed', 'accepted', 'rejected']:
        flash('Invalid status', 'error')
        return redirect(url_for('jobs.job_applications', job_id=application.job_id))
    
    try:
        from datetime import datetime
        application.status = status
        application.review_notes = review_notes if review_notes else None
        if status != 'pending':
            application.reviewed_at = datetime.now()
        db.session.commit()
        
        # FIX: Refresh user to update stats
        db.session.refresh(user)
        
        flash('Application status updated!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error updating status: {str(e)}")
        flash(f'Error updating status: {str(e)}', 'error')
    
    return redirect(url_for('jobs.job_applications', job_id=application.job_id))