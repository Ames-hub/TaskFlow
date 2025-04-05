import lightbulb
import requests
import hikari
import dotenv
import os

plugin = lightbulb.Plugin(__name__)

bulletins_dir = "data/bulletins"
dotenv.load_dotenv(".env")


# noinspection PyMethodMayBeStatic
class msgserver:
    def get_host(self):
        host = os.environ.get("NEWS_SERVER_HOST")
        ip, port = host.split(":")
        return {"ip": ip, "port": port}

    def get_bulletin(self):
        conndata = self.get_host()
        url = f"http://{conndata['ip']}:{conndata['port']}/get_latest"

        try:
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()

            return data
        except requests.exceptions.RequestException:  # Catches the timeout as well
            raise ConnectionError

    def get_and_format_bulletin(self):
        data = self.get_bulletin()
        bulletin = data['bulletin']
        date = data['date']
        issue_number:str = data['issue_number']

        return {
            "title": f"PSA of {date}\nIssue no. {issue_number}",
            "content": bulletin
        }

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=True)
@lightbulb.command(name='news', description="Find out what's new in the bot!", auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def news_cmd(ctx: lightbulb.SlashContext):
    try:
        data = msgserver().get_and_format_bulletin()
    except ConnectionError:
        if os.path.exists('bulletin.txt'):
            with open('bulletin.txt', 'r') as f:
                bulletin = f.read()
            await ctx.respond(
                hikari.Embed(
                    title="Couldn't connect!",
                    description="We couldn't connect to the news server, so we'll give you a stored news report:\n"
                                f"{bulletin}\n\nTo see the latest information, join the [support server](https://discord.gg/HkKAsgvCzt)!"
                )
            )
            return
        else:
            await ctx.respond(
                hikari.Embed(
                    title="Couldn't find it!",
                    description="Sorry, it seems we could not connect to the news server and there is no locally stored news.\n"
                                "Basically; You're in the dark! Join the [support server](https://discord.gg/HkKAsgvCzt) for current information."
                )
            )
            return

    await ctx.respond(
        hikari.Embed(
            title=data['title'],
            description=data['content']
        )
    )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
