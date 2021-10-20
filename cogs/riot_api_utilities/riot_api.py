from typing import Tuple, Union

import requests, code

from cogs.riot_api_utilities.api_dataclasses.spectator import SpectatorData

from .api_dataclasses.match import Match
from .api_dataclasses.match_timeline import MatchTimeline
from .api_dataclasses.summoner import Summoner
from .api_dataclasses.spectator import SpectatorData


class RiotApi:
    """A class for riot api return values"""

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
            "Accept-Language": "en-US,en-GB;q=0.9,en;q=0.8,pl-PL;q=0.7,pl;q=0.6",
            "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://developer.riotgames.com",
            "X-Riot-Token": f"{self.api_token}",
        }

    def summoner_search(self, summoners_name: str) -> Summoner:
        """Generate a dataclass with all the information on a user

        Args:
        -----
            summoners_name (str): Summoner name of a user

        Returns:
        --------
            Summoner: A dataclass containing all the information on the user
        """
        url = f"https://eun1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoners_name}"

        return Summoner.from_dict(requests.get(url, headers=self.headers).json())

    def __get_last_match_id(self, summoners_puuid) -> str:
        """Get the ID of the last match a summonr has played

        Args:
        -----
            summoners_puuid (str): A PUUID of a summoner

        Returns:
        --------
            str: An ID of a last match played by a summoner
        """
        url = f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{summoners_puuid}/ids?start=0&count=1"
        return requests.get(url, headers=self.headers).json()[0]

    def __get_match_data(self, summoners_puuid: str) -> Match:
        """Get the match data of a summoner with specified PUUID

        Args:
        -----
            summoners_puuid (str): A puuid of a summoner for which the matches is to be searched

        Returns:
        --------
            Match: A dataclass containing the information in regards to the match
        """
        match_id: str = self.__get_last_match_id(summoners_puuid)
        url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}"

        return Match.from_dict(requests.get(url, headers=self.headers).json())

    def __get_match_timeline(self, summoners_puuid: str) -> MatchTimeline:
        """Get timeline of a given match

        Args:
        -----
            summoners_puuid (str): A puuid of a summoner for witch the match is to be searched

        Returns:
        -------
            MatchTimeline: A dataclass containing a match timeline
        """
        match_id: str = self.__get_last_match_id(summoners_puuid)
        url = (
            f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
        )

        return MatchTimeline.from_dict(requests.get(url, headers=self.headers).json())

    def summoners_last_game(self, summoners_name: str) -> Tuple[Match, MatchTimeline]:
        """Return all the information in regards to last match of a given player

        Args:
        ----
            summoners_name (str): A name of a summoner for which the data is to be searched

        Returns:
        -------
            Tuple[Match, MatchTimeline]: A tuple containing dataclasses, which have all the information in regards to the match
        """
        summoner = self.summoner_search(summoners_name)

        return self.__get_match_data(summoner.puuid), self.__get_match_timeline(
            summoner.puuid
        )

    def __get_spectator_data(self, summoner_id: int) -> Union[SpectatorData, bool]:
        """Check if summoner is playing and either return False if not, or dataclass containing current match data

        Args:
        -----
            summoner_id (int): An encrypted id of a user

        Returns:
        --------
            Union[SpectatorData, bool]: Either dataclass containing match data or False if summoner not playing
        """
        url = f"https://eun1.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{summoner_id}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 404:
            return False

        return SpectatorData.from_dict(response.json())

    def summoners_current_game(self, summoners_name: str) -> Union[SpectatorData, bool]:
        """Current game data, if available

        Args:
            summoners_name (str): Name of a summoner to search data for

        Returns:
            Union[SpectatorData, bool]: Either data of a game, if available or False, if game is not played
        """
        summoner = self.summoner_search(summoners_name)
        print(summoner.id)
        spectator_data = self.__get_spectator_data(summoner.id)

        if not spectator_data:
            return False

        return spectator_data
