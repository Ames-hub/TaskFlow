import lightbulb
import requests
import urllib3
import hikari
import dotenv
import os

plugin = lightbulb.Plugin(__name__)
dotenv.load_dotenv(".env")

# We're using self-signed certs. Suppress the warnings.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# noinspection PyMethodMayBeStatic
class msgserver:
    def get_host(self):
        host = os.environ.get("NEWS_SERVER_LINK")
        return host

    def get_bulletin(self):
        url = self.get_host()

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
                    title="Fallback Local News!",
                    description="We couldn't connect to the news server, so we'll give you a stored news report:\n\n"
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

    # The below is telemetry. It is not personally identifiable, and is only used to track feature usage.
    # I'm trying to figure out if anyone even uses this functionality.
    telemetry_url = os.environ.get("USAGE_TELEMETRY_URL")
    try:
        # As we can see, it does not send any user data, just a simple GET request.
        requests.get(telemetry_url, timeout=4, verify=False)
    except requests.exceptions.RequestException as err:
        pass  # We don't care if telemetry fails 

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
