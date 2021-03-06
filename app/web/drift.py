from flask import flash, redirect, url_for, render_template, request
from flask_login import login_required, current_user

from app import db
from app.forms.book import DriftForm
from app.libs.email import send_mail
from app.models.dirft import Drift
from app.models.gift import Gift
from . import web

__author__ = '七月'


@web.route('/drift/<int:gid>', methods=['GET', 'POST'])
@login_required
def send_drift(gid):
    current_gift = Gift.query.get_or_404(gid)

    if current_gift.is_yourself_gift(current_user.id):
        flash('这本书是你自己的^_^, 不能向自己索要.')
        return redirect(url_for('web.book_detail', isbn=current_gift.isbn))

    can = current_user.can_send_drift()
    if not can:
        return render_template('not_enough_beans.html', beans=current_user.beans)

    form = DriftForm(request.form)
    if request.method=='POST' and form.validate():
        save_drift(form, current_gift)
        send_mail(current_gift.user.email, '有人想要一本书', 'email/get_gift.html',wisher=current_user, gift=current_gift)

    gifter = current_gift.user.summary
    return render_template('drift.html',
                           gifter=gifter, user_beans=current_user.beans, form=form)


@web.route('/pending')
@login_required
def pending():
    return 'pending'


@web.route('/drift/<int:did>/reject')
@login_required
def reject_drift(did):
    return 'drift/int/reject'


@web.route('/drift/<int:did>/redraw')
def redraw_drift(did):
    return 'drift/<int:did>/redraw'


@web.route('/drift/<int:did>/mailed')
def mailed_drift(did):
    return '/drift/<int:did>/mailed'


def save_drift(drift_form, current_gift):
    with db.auto_commit():
        drift = Drift()
        drift_form.populate_obj(drift)

        drift.gift_id = current_gift.id
        drift.requester_id = current_user.id
        drift.requester_nickname = current_user.nickname
        drift.gifter_nickname = current_gift.user.nickname
        drift.gifter_id = current_gift.user.id

        book = current_gift.book

        drift.book_title = book['title']
        drift.book_author = book['author']
        drift.book_img = book['image']
        drift.isbn = book['isbn']

        current_user.beans -= 1
        db.session.add(drift)