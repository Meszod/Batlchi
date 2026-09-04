# -*- coding: utf-8 -*-
"""Handlers paketi — barcha handlerlarni ro'yxatdan o'tkazadi."""
from telegram.ext import Application

from . import (
    common, contest_create, contest_join, contest_manage, contest_vote,
    contest_referral, contest_media, admin_panel, pro,
)


def register_all(app: Application):
    common.register(app)
    contest_create.register(app)
    contest_join.register(app)
    contest_vote.register(app)
    contest_referral.register(app)
    contest_media.register(app)
    contest_manage.register(app)
    admin_panel.register(app)
    pro.register(app)
