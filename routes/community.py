from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import db
from models.user import User
from models.post import Post
from models.post_like import PostLike
from models.comment import Comment
from utils.file_handler import save_image, delete_file
from datetime import datetime

community_bp = Blueprint('community', __name__, url_prefix='/community')

def check_user_session():
    """Check if user session is valid"""
    if 'user_id' not in session:
        return None
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return None
    
    return user

@community_bp.route('/')
def index():
    """Community feed page"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    # Get page number
    page = request.args.get('page', 1, type=int)
    
    # Get all posts with pagination
    posts_paginated = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=10)
    posts = posts_paginated.items
    
    # Get comment counts and like status for each post
    post_data = {}
    for post in posts:
        post_data[post.id] = {
            'comments': Comment.query.filter_by(post_id=post.id).count(),
            'liked': post.has_user_liked(user.id)
        }
    
    return render_template('community/community.html',
                         user=user, 
                         posts=posts, 
                         post_data=post_data,
                         pagination=posts_paginated)

@community_bp.route('/post/<int:post_id>')
def view_post(post_id):
    """View single post with comments"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.desc()).all()
    liked = post.has_user_liked(user.id)
    
    return render_template('community/post_detail.html', user=user, post=post, comments=comments, liked=liked)

@community_bp.route('/post/new', methods=['GET', 'POST'])
def create_post():
    """Create new post"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        image_data = request.form.get('post_image', '')
        
        if not content:
            flash('Post cannot be empty', 'error')
            return redirect(url_for('community.create_post'))
        
        image_filename = None
        if image_data and image_data.startswith('data:image'):
            try:
                import base64
                import io
                from werkzeug.datastructures import FileStorage
                
                # Extract base64 data
                header, encoded = image_data.split(',', 1)
                data = base64.b64decode(encoded)
                
                # Create file-like object
                img_file = io.BytesIO(data)
                file = FileStorage(
                    stream=img_file,
                    filename='post-image.jpg',
                    content_type='image/jpeg'
                )
                
                # Save image
                success, result = save_image(file, 'posts')
                if success:
                    image_filename = result
                else:
                    flash(f'Error saving image: {result}', 'error')
                    return redirect(url_for('community.create_post'))
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                flash(f'Error processing image: {str(e)}', 'error')
                return redirect(url_for('community.create_post'))
        
        post = Post(
            content=content,
            image_filename=image_filename,
            author_id=user.id
        )
        db.session.add(post)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('community.index'))
    
    return render_template('community/create_post.html', user=user)

@community_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    """Edit post"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    post = Post.query.get_or_404(post_id)
    
    if post.author_id != user.id and not user.is_admin:
        flash('You can only edit your own posts', 'error')
        return redirect(url_for('community.index'))
    
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        image_data = request.form.get('post_image', '')
        
        if not content:
            flash('Post cannot be empty', 'error')
            return redirect(url_for('community.edit_post', post_id=post_id))
        
        post.content = content
        
        # Handle image update
        if image_data and image_data.startswith('data:image'):
            try:
                import base64
                import io
                from werkzeug.datastructures import FileStorage
                
                # Delete old image if exists
                if post.image_filename:
                    delete_file(post.image_filename, 'posts')
                
                # Extract base64 data
                header, encoded = image_data.split(',', 1)
                data = base64.b64decode(encoded)
                
                # Create file-like object
                img_file = io.BytesIO(data)
                file = FileStorage(
                    stream=img_file,
                    filename='post-image.jpg',
                    content_type='image/jpeg'
                )
                
                # Save new image
                success, result = save_image(file, 'posts')
                if success:
                    post.image_filename = result
                else:
                    flash(f'Error saving image: {result}', 'error')
                    return redirect(url_for('community.edit_post', post_id=post_id))
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                flash(f'Error processing image: {str(e)}', 'error')
                return redirect(url_for('community.edit_post', post_id=post_id))
        
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('community.view_post', post_id=post_id))
    
    return render_template('community/edit_post.html', user=user, post=post)

@community_bp.route('/post/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    """Like/Unlike post"""
    user = check_user_session()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    post = Post.query.get_or_404(post_id)
    
    # Check if already liked
    existing_like = PostLike.query.filter_by(post_id=post_id, user_id=user.id).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        post.likes_count -= 1
        action = 'unliked'
    else:
        # Like
        like = PostLike(post_id=post_id, user_id=user.id)
        db.session.add(like)
        post.likes_count += 1
        action = 'liked'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'action': action,
        'likes_count': post.likes_count
    })

@community_bp.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    """Add comment to post"""
    user = check_user_session()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Comment cannot be empty'}), 400
    
    comment = Comment(
        content=content,
        author_id=user.id,
        post_id=post_id
    )
    db.session.add(comment)
    db.session.commit()
    
    flash('Comment added!', 'success')
    return redirect(url_for('community.view_post', post_id=post_id))

@community_bp.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    """Delete post"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    post = Post.query.get_or_404(post_id)
    
    if post.author_id != user.id and not user.is_admin:
        flash('You can only delete your own posts', 'error')
        return redirect(url_for('community.index'))
    
    try:
        # Delete image if exists
        if post.image_filename:
            delete_file(post.image_filename, 'posts')
        
        # Delete all comments associated with post
        Comment.query.filter_by(post_id=post_id).delete()
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting post: {str(e)}', 'error')
    
    return redirect(url_for('community.index'))

@community_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
def delete_comment(comment_id):
    """Delete comment"""
    user = check_user_session()
    if not user:
        return redirect(url_for('auth.login'))
    
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id
    
    if comment.author_id != user.id and not user.is_admin:
        flash('You can only delete your own comments', 'error')
        return redirect(url_for('community.view_post', post_id=post_id))
    
    try:
        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting comment: {str(e)}', 'error')
    
    return redirect(url_for('community.view_post', post_id=post_id))

@community_bp.route('/post/<int:post_id>/likes_count', methods=['GET'])
def get_likes_count(post_id):
    """Return current like and comment counts for a post (used by profile page polling)"""
    post = Post.query.get_or_404(post_id)
    return jsonify({
        'likes_count': post.likes_count,
        'comments_count': len(post.comments)
    })
