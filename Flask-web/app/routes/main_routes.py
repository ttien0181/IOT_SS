# app/routes/main_routes.py
from flask import Blueprint, render_template, jsonify, send_file, request, session
from app.utils.decorator import login_required
from collections import defaultdict

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    return render_template('index.html')

@main_bp.route('/floor/<int:floor_id>')
@login_required
def floor_page(floor_id):
    return render_template('floor.html', floor_id=floor_id)

@main_bp.route('/user')
@login_required
def user():
    return render_template('user.html')

@main_bp.route('/dashboard/<building>/<floor>/<room>')
@login_required
def dashboard(building,floor, room):
    return render_template('dashboard.html',building = building, floor=floor, room = room)

## Route thông tin người dùng
@main_bp.route('/profile')
@login_required
def profile():
    # Chuyển hướng người dùng về trang đăng nhập
    return render_template('profile.html', email = session['email'], create_at = session['create_at'])


