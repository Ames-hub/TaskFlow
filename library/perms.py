from library.botapp import botapp
from library.storage import dataMan
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

# noinspection PyMethodMayBeStatic
class perms:
    @staticmethod
    async def is_privileged(permission, guild_id, user_id):
        if permission is None:
            return True  # Always permitted if no permission is needed
        if guild_id is None:
            raise ValueError("Guild ID can't be None!")
        if user_id is None:
            raise  ValueError("User ID can't be None!")

        guild_id = int(guild_id)
        user_id = int(user_id)

        user_perms = await perms.get_user_permissions(guild_id, user_id)

        if permission in user_perms:
            return True
        else:
            if hikari.Permissions.ADMINISTRATOR in user_perms:
                return True
            return False

    @staticmethod
    async def get_user_permissions(guild_id, user_id):
        user_id = int(user_id)
        guild_id = int(guild_id)

        member:hikari.Member = await plugin.bot.rest.fetch_member(guild=guild_id, user=user_id)

        # If the user is the owner of the guild, return all permissions.
        owner_id = perms.get_guild_owner_id(guild_id)

        if owner_id == member.id:
            return hikari.Permissions.all_permissions()

        perms_list = []
        roles = await member.fetch_roles()
        for role in roles:
            for perm in role.permissions:
                if perm not in perms_list:
                    perms_list.append(perm)
                else:
                    continue

        return perms_list

    @staticmethod
    async def get_guild_owner_id(guild_id):

        if plugin.bot.d['guild_owner_ids_cache'].get(guild_id, None) is None:
            guild = botapp.cache.get_guild(guild_id)
            if guild is not None:
                owner_id = guild.owner_id
            else:
                guild = await plugin.bot.rest.fetch_guild(guild_id)
                owner_id = guild.owner_id
            plugin.bot.d['guild_owner_ids_cache'][guild_id] = owner_id
        else:
            owner_id = plugin.bot.d['guild_owner_ids_cache'][guild_id]

        return int(owner_id)

    @staticmethod
    async def can_configure_bot(guild_id:int, user_id:int):
        guild_conf_perm = dataMan().get_guild_configperm(guild_id)
        user_perms = await perms.get_user_permissions(guild_id, user_id)

        can_configure = guild_conf_perm in user_perms
        if not can_configure:
            if hikari.Permissions.ADMINISTRATOR in user_perms:
                return True
        return can_configure

    @staticmethod
    async def can_interact_tasks(guild_id:int, user_id:int):
        user_id = int(user_id)
        guild_id = int(guild_id)

        member:hikari.Member = await plugin.bot.rest.fetch_member(guild=guild_id, user=user_id)
        taskhelper_role_id = dataMan().get_taskmaster_role(guild_id)

        if taskhelper_role_id is not None:
            # The task interaction has been locked to a role by admins. Check if the user has the role.
            roles = member.get_roles()
            guild_owner_id = await perms.get_guild_owner_id(guild_id)
            if guild_owner_id == user_id:
                return True
            for role in roles:
                # Allow admins and task helpers
                if hikari.Permissions.ADMINISTRATOR in role.permissions:
                    return True
                if role.id == taskhelper_role_id:
                    return True
            return False
        else:
            # The interactions haven't been locked to a role. Allow all
            return True

    class embeds:
        @staticmethod
        async def insufficient_perms(interaction_context:lightbulb.Context|lightbulb.SlashContext, missing_perm=None):
            """
            Builds an embed and responds to the interaction context with it.
            :param interaction_context: The slash context for the command.
            :param missing_perm:
            :return:
            """
            embed = hikari.Embed(
                title="Unauthorized",
                description=f"You need {missing_perm} permission to be able to do that." if missing_perm else "You do not have the needed permission to do that."
            )
            await interaction_context.respond(embed)

        @staticmethod
        def gen_interaction_tasks_embed():
            return (
                hikari.Embed(
                    title="Unauthorized",
                    description="Sorry, in this server, you need a specific role that was set by administration to interact with tasks."
                )
            )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
