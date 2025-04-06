from library.storage import dataMan
import lightbulb
import hikari
import miru

plugin = lightbulb.Plugin(__name__)

class SetDescModal(miru.Modal, title="Set Description"):

    description = miru.TextInput(
        label="Description",
        placeholder="Please set the description",
        required=True,
        style=hikari.TextInputStyle.PARAGRAPH
    )

    # The callback function is called after the user hits 'Submit'
    async def callback(self, ctx: miru.ModalContext) -> None:
        desc = self.description.value.strip()
        dm = dataMan()

        success = dm.set_livelist_description(desc, ctx.guild_id)

        if success:
            await ctx.respond(
                hikari.Embed(
                    title="Description set",
                    description="The description has been successfully set to what you entered."
                )
                .add_field(
                    name="Placeholders",
                    value="Placeholders to enter data into the description coming soon."
                ),
                flags=hikari.MessageFlag.EPHEMERAL
            )
        else:
            await ctx.respond(
                hikari.Embed(
                    title="Uh oh!",
                    description="Something went wrong and we couldn't do it! :( We're tracking the error now."
                ),
                flags=hikari.MessageFlag.EPHEMERAL
            )