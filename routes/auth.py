"""
文芽 - 认证路由
"""
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timezone

from app import db, limiter
from models.user import User, UserProfile
from models.writing import Writing
from models.compliance import ComplianceLog
from utils.validators import validate_password, validate_grade
from utils.response import success_response, error_response
from utils.helpers import get_client_ip
from services.content_safe import ContentSafeService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per hour")
def login():
    """用户登录"""
    data = request.get_json()
    if not data:
        return error_response('Invalid request', status_code=400)

    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return error_response('用户名和密码不能为空', status_code=400)

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return error_response('用户名或密码错误', status_code=401)

    if not user.is_active:
        return error_response('账号已被停用', status_code=403)

    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()

    login_user(user, remember=bool(data.get('remember', False)))

    compliance_log = ComplianceLog(
        log_type='user_action',
        user_id=user.id,
        action='user_login',
        details={'username': username},
        ip_address=get_client_ip()
    )
    db.session.add(compliance_log)
    db.session.commit()

    return success_response({'user': user.to_dict()}, message='登录成功')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    compliance_log = ComplianceLog(
        log_type='user_action',
        user_id=current_user.id,
        action='user_logout',
        ip_address=get_client_ip()
    )
    db.session.add(compliance_log)
    db.session.commit()

    logout_user()
    return success_response(message='已退出登录')


@auth_bp.route('/change-password', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def change_password():
    """修改密码"""
    data = request.get_json()
    if not data:
        return error_response('Invalid request', status_code=400)

    old_password = data.get('old_password') or ''
    new_password = data.get('new_password') or ''

    if not current_user.check_password(old_password):
        return error_response('原密码错误', status_code=400)

    ok, msg = validate_password(new_password)
    if not ok:
        return error_response(msg, status_code=400)

    if old_password == new_password:
        return error_response('新密码不能与原密码相同', status_code=400)

    current_user.set_password(new_password)
    db.session.commit()

    compliance_log = ComplianceLog(
        log_type='user_action',
        user_id=current_user.id,
        action='password_change',
        ip_address=get_client_ip()
    )
    db.session.add(compliance_log)
    db.session.commit()

    return success_response(message='密码修改成功')


@auth_bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile():
    """获取/更新用户资料"""
    if request.method == 'GET':
        guardian = current_user.guardian if current_user.guardian_id else None
        return success_response({
            'user': current_user.to_dict(),
            'profile': current_user.profile.to_dict() if current_user.profile else None,
            # 监护人信息只返回脱敏字段
            'guardian': {
                'name': guardian.name,
                'relationship': guardian.relationship,
                'phone_masked': guardian.phone[:3] + '****' + guardian.phone[-4:] if guardian.phone else None,
                'is_verified': guardian.is_verified,
                'consent_given_at': guardian.consent_given_at.isoformat() if guardian.consent_given_at else None
            } if guardian else None
        })

    # PUT - 更新资料
    data = request.get_json()
    if not data:
        return error_response('Invalid request', status_code=400)

    if 'nickname' in data:
        nickname = (data.get('nickname') or '').strip()
        if len(nickname) > 32:
            return error_response('昵称最多 32 个字符', status_code=400)
        if nickname:
            safety = ContentSafeService().check_content(nickname)
            if not safety['is_safe']:
                return error_response('昵称包含不当内容', status_code=400)
        current_user.nickname = nickname or None

    for field in ('show_in_ranking', 'show_works_publicly'):
        if field in data:
            if not isinstance(data[field], bool):
                return error_response(f'{field} 必须为布尔值', status_code=400)
            setattr(current_user, field, data[field])

    if 'grade' in data:
        ok, msg = validate_grade(data['grade'])
        if not ok:
            return error_response(msg, status_code=400)
        current_user.grade = data['grade']

    db.session.commit()
    return success_response({'user': current_user.to_dict()}, message='资料更新成功')


@auth_bp.route('/export-data', methods=['POST'])
@login_required
@limiter.limit("3 per day")
def export_data():
    """导出用户数据（合规要求：数据可携带权）"""
    writings = Writing.query.filter_by(user_id=current_user.id).all()
    profile = current_user.profile

    export = {
        'user': current_user.to_dict(),
        'profile': profile.to_dict() if profile else None,
        'writings': [w.to_dict(include_content=True, include_scores=True) for w in writings],
        'exported_at': datetime.now(timezone.utc).isoformat()
    }

    compliance_log = ComplianceLog(
        log_type='compliance',
        user_id=current_user.id,
        action='data_export',
        ip_address=get_client_ip()
    )
    db.session.add(compliance_log)
    db.session.commit()

    return success_response(export, message='数据导出成功')


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """获取当前用户信息"""
    return success_response({
        'user': current_user.to_dict(),
        'profile': current_user.profile.to_dict() if current_user.profile else None
    })
