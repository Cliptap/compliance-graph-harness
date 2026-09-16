from contextvars import ContextVar

current_user_ctx: ContextVar[str] = ContextVar("current_user", default="system")
