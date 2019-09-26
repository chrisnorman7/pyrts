"""Provides the task decorator."""

import logging

from twisted.internet.task import LoopingCall

logger = logging.getLogger(__name__)


def task(interval, now=True):
    """Decorate a function to be called at a regular interval. Both interval
    and now are passed to LoopingCall.start."""

    def inner(func):
        t = LoopingCall(func)
        t.start(interval, now=now)
        logger.info('Created task %r at interval %d.', func, interval)
        return t

    return inner
