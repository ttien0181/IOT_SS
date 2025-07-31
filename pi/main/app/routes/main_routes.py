# app/routes/main_routes.py
from flask import Blueprint, render_template
from app.utils.decorator import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    return render_template('index.html')

@main_bp.route('/floor/<int:floor_id>')
@login_required
def floor_page(floor_id):
    return render_template('floor.html', floor_id=floor_id)

@main_bp.route('/')
@login_required
def user():
    return render_template('user.html')
