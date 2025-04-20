from library.storage import dataMan
import hikari
import miru


class main_view:
    def __init__(self, template_id):
        self.template_Id = template_id

    def init_view(self):
        template_id = self.template_Id
        class Menu_Init(miru.View):
            # noinspection PyUnusedLocal
            @miru.button(label="Do not delete", style=hikari.ButtonStyle.SUCCESS)
            async def stop_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
                await ctx.edit_response(
                    hikari.Embed(
                        title="Deletion cancelled.",
                        description="All assosciated tasks have not been removed."
                    ),
                    components=[]
                )
                self.stop()  # Called to stop the view

            # noinspection PyUnusedLocal
            @miru.button(label="Delete template", style=hikari.ButtonStyle.DANGER)
            async def delete_btn(self, ctx: miru.ViewContext, select: miru.Button) -> None:
                success = dataMan().delete_task_template(identifier=template_id)
                if success:
                    await ctx.edit_response(
                        hikari.Embed(
                            title="Template deleted!",
                            description="All assosciated tasks have been removed."
                        ),
                        components=[]
                    )
                else:
                    await ctx.edit_response(
                        hikari.Embed(
                            title="Template deletion failed!",
                            description="Something went wrong! Please try again in a moment."
                        ),
                        components=[]
                    )

        return Menu_Init()