import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import all models so their tables are created.
from storage.api_key import ApiKey  # noqa: F401
from storage.base import Base
from storage.billing_session import BillingSession  # noqa: F401
from storage.conversation_work import ConversationWork  # noqa: F401
from storage.device_code import DeviceCode  # noqa: F401
from storage.feedback import Feedback  # noqa: F401
from storage.github_app_installation import GithubAppInstallation  # noqa: F401
from storage.org import Org  # noqa: F401
from storage.org_git_claim import OrgGitClaim  # noqa: F401
from storage.org_invitation import OrgInvitation  # noqa: F401
from storage.org_member import OrgMember  # noqa: F401
from storage.role import Role  # noqa: F401
from storage.slack_conversation import SlackConversation  # noqa: F401
from storage.stored_conversation_metadata import (
    StoredConversationMetadata,  # noqa: F401
)
from storage.stored_conversation_metadata_saas import (  # noqa: F401
    StoredConversationMetadataSaas,
)
from storage.stored_offline_token import StoredOfflineToken  # noqa: F401
from storage.stripe_customer import StripeCustomer  # noqa: F401
from storage.user import User  # noqa: F401
from storage.user_settings import UserSettings  # noqa: F401


@pytest.fixture(autouse=True)
def allow_short_context_windows():
    old = os.environ.get('ALLOW_SHORT_CONTEXT_WINDOWS')
    os.environ['ALLOW_SHORT_CONTEXT_WINDOWS'] = 'true'
    try:
        yield
    finally:
        if old is None:
            os.environ.pop('ALLOW_SHORT_CONTEXT_WINDOWS', None)
        else:
            os.environ['ALLOW_SHORT_CONTEXT_WINDOWS'] = old


@pytest.fixture(scope='function')
def db_path(tmp_path):
    """Create a unique temp file path for each test."""
    return str(tmp_path / 'test.db')


@pytest.fixture
def engine(db_path):
    """Create a sync engine with tables using file-based DB."""
    engine = create_engine(
        f'sqlite:///{db_path}', connect_args={'check_same_thread': False}
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session_maker(engine):
    return sessionmaker(bind=engine)


@pytest.fixture
def async_engine(db_path):
    """Create an async engine using the SAME file-based database."""
    async_engine = create_async_engine(
        f'sqlite+aiosqlite:///{db_path}',
        connect_args={'check_same_thread': False},
    )

    async def create_tables():
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    import asyncio

    asyncio.run(create_tables())
    return async_engine


@pytest.fixture
async def async_session_maker(async_engine):
    """Create an async session maker bound to the async engine."""
    return async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
