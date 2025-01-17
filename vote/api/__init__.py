from typing import Annotated
from surrealdb import Surreal
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseSettings
import toml

from vote.domain.user import UserRepository, UserRepositoryImpl, UserService
from vote.domain.topic import TopicService, TopicRepositoryImpl
from vote.domain.vote import VoteService, VoteRepositoryImpl
from vote.domain.auth import AuthConfig, AuthService

oauth2_schema = OAuth2PasswordBearer(tokenUrl='/auth/token')


def toml_settings(settings: BaseSettings) -> dict:
    return toml.load(open(settings.__config__.path))


# https://docs.pydantic.dev/latest/usage/settings/#customise-settings-sources
class VoteConfigToml(BaseSettings):
    '''
    Config for vote app loading from a toml file
    '''
    auth: AuthConfig

    class Config:
        path = 'vote.toml'

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                toml_settings,
                env_settings,
                file_secret_settings,
            )


def get_vote_config():
    return VoteConfigToml()


async def get_db():
    db = Surreal('ws://localhost:8080/rpc')
    async with db as db:
        # TODO: load config
        await db.signin({'user': 'root', 'pass': 'root'})
        await db.use('vote', 'vote')
        yield db


async def get_user_repository(db: Annotated[
    Surreal,
    Depends(get_db),
]):
    repo = UserRepositoryImpl(db)
    await repo.init_db()
    return repo


async def get_user_service(repo: Annotated[
    UserRepository,
    Depends(get_user_repository),
]):
    return UserService(repo)


async def get_topic_service(db: Annotated[
    Surreal,
    Depends(get_db),
]):
    return TopicService(TopicRepositoryImpl(db))


async def get_vote_service(db: Annotated[
    Surreal,
    Depends(get_db),
]):
    repo = VoteRepositoryImpl(db)
    await repo.init_db()
    return VoteService(repo)


def get_auth_service(cfg: Annotated[
    VoteConfigToml,
    Depends(get_vote_config),
]):
    return AuthService(cfg.auth)
