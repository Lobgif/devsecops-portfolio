# Alembic env unique — importe tous les modèles puis migre tous les schémas.
import agoraci.auth.models  # noqa: F401
import agoraci.forum.models  # noqa: F401
import agoraci.rag.models  # noqa: F401
import agoraci.notification.models  # noqa: F401
import agoraci.messages.models  # noqa: F401
import agoraci.core.models  # noqa: F401
from agoraci.common.migrations import run_migrations

run_migrations()
