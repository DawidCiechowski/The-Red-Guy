from abc import ABC, abstractmethod
import io
from datetime import datetime
from enum import Enum

import discord
from discord.embeds import Embed
import matplotlib.pyplot as plt
from PIL import Image

from cogs.riot_api_utilities.riot_api import RiotApi
from cogs.riot_api_utilities.api_dataclasses.champion import champions_data


class UnknownTypeException(Exception):
    """Raised when factory is given an unknown type"""


class EmbedType(Enum):
    DAMAGE = "damage"
    KDA = "kda"
    DEFENSE = "defense"
    SUMMONER = "summoner"
    KILL_PARTICIPATION = "kp"
    SPECTATE = "spectate"


class ApiEmbed(ABC):
    @abstractmethod
    def create_embed(self) -> discord.Embed:
        pass

    def _figure_to_image(self, figure) -> Image:
        """Protected function, converting matplotlib figure into pillow Image

        Args:
            figure (matplotlib.pyplot.figure): Matplotlib figure

        Returns:
            Image: A figure converted into pillow Image
        """

        data_stream = io.BytesIO()
        figure.savefig(data_stream)
        data_stream.seek(0)
        image = Image.open(data_stream)
        return image

    @staticmethod
    def _convert_unix_timestamp(timestamp: int) -> str:
        return datetime.utcfromtimestamp(timestamp / 1000).strftime("%H:%M %d-%m-%y")


class DamageEmbedApi(ApiEmbed):
    def __init__(self, api: RiotApi, summoner: str):
        self.api = api
        self.summoner = summoner

    def create_embed(self) -> discord.Embed:
        summoner = self.api.summoner_search(self.summoner)
        matches, _ = self.api.get_summoner_games(self.summoner)
        matches_dates = []
        damage_stats = []

        for match in matches:
            for participant in match.info.participants:

                if summoner.puuid == participant.puuid:
                    damage_stats.append(participant.total_damage_dealt_to_champions)

            matches_dates.append(
                self._convert_unix_timestamp(match.info.game_start_timestamp)
            )

        figure = plt.figure()

        plt.bar(matches_dates[::-1], damage_stats[::-1], color="maroon", width=0.5)
        # Rotate x labels by 30 degrees
        figure.autofmt_xdate(ha="right")

        pil_image = self._figure_to_image(figure)
        pil_image.save("test.png")
        embed = discord.Embed(
            title="Damage",
            description=f"Damage zadany przez: {summoner.name}",
            color=discord.Color.blue(),
        )
        embed.set_image(url="attachment://image.png")

        plt.clf()

        return embed


class DefenseEmbedApi(ApiEmbed):
    def __init__(self, api: RiotApi, summoner: str):
        self.api = api
        self.summoner = summoner

    def create_embed(self) -> discord.Embed:
        summoner = self.api.summoner_search(self.summoner)
        matches, _ = self.api.get_summoner_games(self.summoner)
        matches_dates = []
        defensive_stats = []

        for match in matches:
            for participant in match.info.participants:

                if summoner.puuid == participant.puuid:
                    defensive_stats.append(
                        participant.total_damage_taken
                        + participant.damage_self_mitigated
                    )

            matches_dates.append(
                self._convert_unix_timestamp(match.info.game_start_timestamp)
            )

        figure = plt.figure()

        plt.bar(matches_dates[::-1], defensive_stats[::-1], color="darkblue", width=0.5)
        # Rotate x labels by 30 degrees
        figure.autofmt_xdate(ha="right")
        plt.ylabel("Damage przyjety")
        plt.title(f"Damage przyjety przez: {summoner.name}")
        pil_image = self._figure_to_image(figure)
        pil_image.save("test.png")
        embed = discord.Embed(
            title="Def",
            description=f"Damage przyjety przez: {summoner.name}",
            color=discord.Color.blue(),
        )
        embed.set_image(url="attachment://image.png")

        plt.clf()

        return embed


class KdaEmbedApi(ApiEmbed):
    def __init__(self, api: RiotApi, summoner: str) -> None:
        self.api = api
        self.summoner = summoner

    def create_embed(self) -> discord.Embed:
        summoner = self.api.summoner_search(self.summoner)
        matches, _ = self.api.get_summoner_games(self.summoner)
        kills, deaths, assists = [], [], []
        matches_dates = []

        for match in matches:
            [
                (
                    kills.append(participant.kills),
                    deaths.append(participant.deaths),
                    assists.append(participant.assists),
                )
                for participant in match.info.participants
                if participant.puuid == summoner.puuid
            ]

            matches_dates.append(self._convert_unix_timestamp(match.info.game_creation))

        if kills and deaths and assists:
            plt.plot(matches_dates[::-1], kills[::-1], "b--", label="Kills")
            plt.plot(matches_dates[::-1], deaths[::-1], "r--", label="Deaths")
            plt.plot(matches_dates[::-1], assists[::-1], "g:", label="Assists")
            plt.legend()

        figure = plt.gcf()
        # Rotate x labels by 30 degrees
        figure.autofmt_xdate(ha="right")

        plt.title(
            f"KDA: Srednie = {round(sum(kills)/len(kills), 1)}/{round(sum(deaths)/len(deaths), 1)}/{round(sum(assists)/len(assists), 1)}"
        )
        pil_image = self._figure_to_image(figure)
        pil_image.save("test.png")
        embed = discord.Embed(
            title="KDA",
            description=f"KDA dla {summoner.name}",
            color=discord.Color.blue(),
        )
        embed.set_image(url="attachment://image.png")

        plt.clf()

        return embed


class SummonerEmbedApi(ApiEmbed):
    def __init__(self, api: RiotApi, summoner: str):
        self.api = api
        self.summoner = summoner

    def create_embed(self) -> discord.Embed:
        try:
            summoner_data = self.api.summoner_search(self.summoner)
        except Exception as err:
            return "LOL"
        match, _ = self.api.summoners_last_game(self.summoner)
        match_timestamp = self._convert_unix_timestamp(match.info.game_creation)
        game_mode = match.info.game_mode
        damage_chart = []
        damage_taken_chart = []
        for participant in match.info.participants:
            damage_chart.append(participant.total_damage_dealt_to_champions)
            damage_taken_chart.append(
                participant.total_damage_taken + participant.damage_self_mitigated
            )
            if summoner_data.puuid == participant.puuid:
                role = participant.role
                minions = participant.total_minions_killed
                deaths = participant.deaths
                assists = participant.assists
                kills = participant.kills
                win = "Tak" if participant.win else "Nie"
                champion = participant.champion_name
                total_damage_to_champions = participant.total_damage_dealt_to_champions
                wards_placed = participant.wards_placed
                total_damage_taken = (
                    participant.total_damage_taken + participant.damage_self_mitigated
                )
                self_healed_damage = (
                    participant.total_heal - participant.total_heals_on_teammates
                )
                teammate_healed_damage = participant.total_heals_on_teammates
                true_damage_dealt = participant.true_damage_dealt_to_champions
                magic_damage_dealt = participant.magic_damage_dealt_to_champions
                physical_damage_dealt = participant.physical_damage_dealt_to_champions

        damage_chart.sort(reverse=True)
        damage_index = damage_chart.index(total_damage_to_champions) + 1

        damage_taken_chart.sort(reverse=True)
        damage_taken_index = damage_taken_chart.index(total_damage_taken) + 1

        embed_title = "__SUMMONER SEARCH__"
        embed_message = f"""
```ini
[Generalne informacje]```
                            
                            **Nick**: {summoner_data.name}
                            **Poziom:** {summoner_data.summoner_level}
                            **Ostatni Mecz:** {match_timestamp}\n**Mode:** {game_mode}
                            **KDA:** {kills}/{deaths}/{assists}\n**Wygrana:** {win}
                            **Miniony:** {minions}
                            **Champ:** {champion}
                            **Rola:** {role}
                            
```fix
Informacje ofensywne```
                            
                            **Dmg calkowity zadany innym:** {total_damage_to_champions}
                            **Miejsce pod wzgledem dmg:** {damage_index}
                            **Zadany dmg magiczny:** {magic_damage_dealt}
                            **Zadany dmg fizyczny:** {physical_damage_dealt}
                            **Zadany true dmg:** {true_damage_dealt}
                            
```fix
=Informacje defensywne```
                            
                            **Calkowity dmg przyjety:** {total_damage_taken}
                            **Miejsce pod wzgledem przyjetego dmg:** {damage_taken_index}
                            **Dmg wyleczony:** {self_healed_damage}
                            **Teammaci wyleczeni:** {teammate_healed_damage}
                            **Polozone wardy**: {wards_placed}
                            """

        embed =  discord.Embed(
            title=embed_title, description=embed_message, color=discord.Color.blue(), url=''
        )

        splash_url = f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{champion}_1.jpg"
        embed.set_image(url=splash_url)
        return embed


class SpectateEmbedApi(ApiEmbed):
    def __init__(self, api: RiotApi, summoner: str):
        self.api = api
        self.summoner = summoner

    def create_embed(self) -> discord.Embed:
        """Generate a discord.Embed from spectate data.
        Ritos api is so freeaking baaaad, it literally doesnt give any useful information

        Args:
        -----
            summoner_name (str): A name of a summoner, to search data for

        Returns:
        -------
            discord.Embed: An embedded message generated from data, or a simple embed showcasing the player is not currently in-game
        """
        game_data = self.api.summoners_current_game(self.summoner)
        if not game_data:
            return False

        # ------------------------ Game Data -----------------------------------
        summoner_data = [
            participant
            for participant in game_data.participants
            if participant.summoner_name.lower() == self.summoner.lower()
        ][0]

        champ_data = [value for value in champions_data.data.values() if int(value.key) == summoner_data.champion_id][0]
        title = "__Tracker__"
        description = f"```ini\n[Generalne Informacje]```\n\n**Nick:** {summoner_data.summoner_name}  \n\n**Mode:** {game_data.game_mode} \n\n**Gra:** {champ_data.name}"
    

        embed = discord.Embed(title=title, description=description, color=discord.Color.dark_blue())
        return embed


class KillParticipationEmbedApi(ApiEmbed):
    def __init__(self, api: RiotApi, summoner: str):
        self.api = api
        self.summoner = summoner

    def create_embed(self) -> discord.Embed:
        summoner = self.api.summoner_search(self.summoner)
        matches, _ = self.api.get_summoner_games(self.summoner)
        matches_dates = []
        kp = []

        team_id = None
        team_kills = None
        summoner_ka = None

        for match in matches:
            for participant in match.info.participants:
                if participant.puuid == summoner.puuid:
                    team_id = participant.team_id
                    summoner_ka = participant.kills + participant.assists

            team_kills = [
                team.objectives.champion.kills
                for team in match.info.teams
                if team.team_id == team_id
            ][0]
            kp.append(round(summoner_ka / team_kills * 100, 1))
            matches_dates.append(self._convert_unix_timestamp(match.info.game_creation))

        figure = plt.figure()

        plt.bar(matches_dates[::-1], kp[::-1], color="darkslategray", width=0.5)
        # Rotate x labels by 30 degrees
        figure.autofmt_xdate(ha="right")
        plt.ylabel("% Kill Participation")

        pil_image = self._figure_to_image(figure)
        pil_image.save("test.png")
        embed = discord.Embed(
            title="Kill Participation",
            description=f"Kill participation %: {summoner.name}",
            color=discord.Color.blue(),
        )
        embed.set_image(url="attachment://image.png")

        plt.clf()

        return embed


class EmbedFactory:
    @staticmethod
    def factory_embed(embed_type: EmbedType, api: RiotApi, summoner: str) -> ApiEmbed:
        if embed_type == EmbedType.DAMAGE:
            return DamageEmbedApi(api, summoner)
        if embed_type == EmbedType.DEFENSE:
            return DefenseEmbedApi(api, summoner)
        if embed_type == EmbedType.KDA:
            return KdaEmbedApi(api, summoner)
        if embed_type == EmbedType.SUMMONER:
            return SummonerEmbedApi(api, summoner)
        if embed_type == EmbedType.SPECTATE:
            return SpectateEmbedApi(api, summoner)
        if embed_type == EmbedType.KILL_PARTICIPATION:
            return KillParticipationEmbedApi(api, summoner)
        
        raise UnknownTypeException(f"{type} doesn't exists within factory")
