from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta

from extensions import db
from models import Notification

bp = Blueprint('notification', __name__)


@bp.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # --- filtering & pagination -------------------------------
    page        = request.args.get('page', 1, type=int)
    base_q      = Notification.query.filter_by(user_id=session['user_id'])
    if request.args.get('filter') == 'unread':
        base_q = base_q.filter_by(is_read=False)
    if request.args.get('type'):
        base_q = base_q.filter_by(notification_type=request.args['type'])

    notifications = base_q.order_by(Notification.created_at.desc()) \
                          .paginate(page=page, per_page=20, error_out=False)

    # --- date cut-offs that the template will use --------------
    now            = datetime.utcnow()
    today_start    = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start= today_start - timedelta(days=1)
    week_ago       = today_start - timedelta(days=7)

    return render_template(
        'common/notifications.html',
        notifications   = notifications,
        today_start     = today_start,
        yesterday_start = yesterday_start,
        week_ago        = week_ago
    )


@bp.route('/notifications/mark_read/<int:notification_id>')
def mark_notification_read(notification_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    notification = Notification.query.filter_by(
        id=notification_id, user_id=session['user_id']
    ).first()
    
    if notification:
        notification.is_read = True
        db.session.commit()
        
        if notification.action_url:
            return redirect(notification.action_url)
    
    return redirect(url_for('notification.notifications'))


@bp.route('/notifications/mark_all_read', methods=['POST'])
def mark_all_notifications_read():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Mark all unread notifications as read
    Notification.query.filter_by(
        user_id=session['user_id'], is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    
    # Return to the same page
    return redirect(url_for('notification.notifications'))
