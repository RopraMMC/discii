import json
import sys
import aiohttp

from asyncio import AbstractEventLoop
from aiohttp import ClientSession, ClientWebSocketResponse
from typing import Dict, Any, TYPE_CHECKING

from . import __version__
from .message import Message
from .user import User

if TYPE_CHECKING:
    from .cache import Cache
    from .client import Client

# fmt: off
__all__ = (
    'HTTPClient',
    'Route'
)
# fmt: on


class Route:
    """
    Represents an api route which contains
    information about the call, including
    method and path.

    Parameters
    ----------
    method: :class:`str`
        The method to send to the api.
    path: :class:`str`
        The api path to send the data to.

    Attributes
    ----------
    BASE_URL: :class:`str`
        The base api url.
    """

    BASE_URL = "https://discord.com/api/v9"

    def __init__(self, method: str, path: str) -> None:
        self.method = method
        self.path = self.BASE_URL + path


class HTTPClient:
    """
    Represents the HTTP client that manages
    interactions to the discord api which
    entails sending custom requests with bot
    specific authorization headers.

    Parameters
    ----------
    token: :class:`str`
        The bot token to pass through the
        authorization headers while interacting
        with the discord api.
    loop: :class:`AbstractEventLoop`
        The event loop that all tasks run from.
    cache: :class:`Cache`
        The cache that holds info.
    _session: :class:`ClientSession`
        The session to make requests from
        and to handle interactions with the api.
    user_agent: :class:`str`
        The user agent to pass through authorization
        so that the discord api is less suspicious.
    """

    def __init__(
        self,
        *,
        token: str,
        loop: AbstractEventLoop,
        session: ClientSession,
        client: "Client"
    ) -> None:
        self.token: str = token
        self.loop: AbstractEventLoop = loop
        self.client: "Client" = client
        self.cache: "Cache" = client._cache
        self._session: ClientSession = session

        user_agent = "DiscordBot (https://github.com/CaedenPH/discii {0}) Python/{1[0]}.{1[1]} aiohttp/{2}"
        self.user_agent: str = user_agent.format(
            __version__, sys.version_info, aiohttp.__version__
        )

    async def ws_connect(self, gateway_url: str) -> ClientWebSocketResponse:
        """
        Connects to the gateway.

        Parameters
        ----------
        gateway_url: :class:`str`
            The gateway url to connect to.
        """
        return await self._session.ws_connect(gateway_url)

    async def request(self, route: Route, **kwargs: Any) -> Any:
        """
        Sends a request through the session

        Parameters
        ----------
        route: :class:`Route`
            The route class which contains the
            method and path of the request.
        kwargs: :class:`Dict[Any, Any]`
            The dict containing the information
            to be passed into the request. If found,
            the json param will be auto-converted to
            the headers passed.
        """

        headers: Dict = {"User-Agent": self.user_agent}
        headers["Authorization"] = "Bot " + self.token

        if "json" in kwargs:
            headers["Content-Type"] = "application/json"
            kwargs["data"] = json.dumps(kwargs.pop("json"))

        kwargs["headers"] = headers

        async with self._session.request(route.method, route.path, **kwargs) as req:
            return await req.json()

    async def send_message(self, channel_id: int, **kwargs) -> Message:
        route = Route(
            "POST", "/channels/{channel_id}/messages".format(channel_id=channel_id)
        )

        if kwargs["embeds"]:
            embeds = [embed._to_dict() for embed in kwargs["embeds"]]
        else:
            embeds = None

        payload = {
            "content": kwargs["content"] or None,
            "embeds": embeds,
            "message_reference": kwargs.get("message_reference", None),
        }

        try:
            raw_message = await self.request(route, json=payload)
        except Exception as e:
            raw_message = {"_": 1}  # appeasing the typechecker while in testing stage
            print("uh " + str(e))

        message = Message(payload=raw_message, state=self.client._get_state())
        return message

    async def delete_message(self, message_id: int, channel_id: int) -> None:
        route = Route(
            "DELETE",
            "/channels/{channel_id}/messages/{message_id}".format(
                channel_id=channel_id,
                message_id=message_id,
            ),
        )
        await self.request(route)

    async def create_dm(self, user_id: int) -> int:
        route = Route(
            "POST",
            "/users/@me/channels"
        )
        request = await self.request(route, json={"recipient_id": user_id})

        user = User(payload=request["recipients"][0], state=self.client._get_state())
        self.cache.add_user(user)

        return request["id"]