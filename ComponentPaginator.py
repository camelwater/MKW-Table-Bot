import discord
from discord.ext import pages as ext_pages

from discord import abc
from discord.commands import ApplicationContext
from discord.ext.commands import Context
from typing import Optional, List, Union, Dict


class PaginatorButton(discord.ui.Button):
    """Creates a button used to navigate the paginator.

    Parameters
    ----------
    button_type: :class:`str`
        The type of button being created.
        Must be one of ``first``, ``prev``, ``next``, or ``last``.
    paginator: :class:`Paginator`
        The paginator class where this button will be used.
    """

    def __init__(self, label, emoji, style, disabled, button_type, paginator: 'SuggestionsPaginator'):
        super().__init__(label=label, emoji=emoji, style=style, disabled=disabled, row=4)
        self.label = label
        self.emoji = emoji
        self.style = style
        self.disabled = disabled
        self.button_type = button_type
        self.paginator = paginator

    async def callback(self, interaction: discord.Interaction):
        if self.button_type == "first":
            self.paginator.current_page = 0
        elif self.button_type == "prev":
            self.paginator.current_page -= 1
        elif self.button_type == "next":
            self.paginator.current_page += 1
        elif self.button_type == "last":
            self.paginator.current_page = self.paginator.page_count
        await self.paginator.goto_page(interaction=interaction, page_number=self.paginator.current_page)


class SuggestionsPaginator(discord.ui.View):
    '''
    Paginator from `pycord` with only the buttons changed
    '''
    def __init__(
        self,
        pages: Union[List[str], List[discord.Embed]],
        views: List[discord.ui.View],
        show_disabled=True,
        show_indicator=True,
        author_check=True,
        disable_on_timeout=True,
        custom_view: Optional[discord.ui.View] = None,
        timeout: Optional[float] = 180.0,
    ):
        super().__init__(timeout=timeout)

        self.bot = None
        self.prefix = None
        self.error = None
        self.lounge = None
        self.index = None
        self.selected_values = None
        self.messages = pages
        self.done = [False]*len(pages)

        self.timeout = timeout
        self.pages = pages
        self.views = views
        self.current_page = 0
        self.page_count = len(self.pages) - 1
        self.show_disabled = show_disabled
        self.show_indicator = show_indicator
        self.disable_on_timeout = disable_on_timeout
        self.custom_view = custom_view
        self.message: Union[discord.Message, discord.WebhookMessage, None] = None
        self.buttons = {
            "first": {
                "object": PaginatorButton(
                    label="<<",
                    style=discord.ButtonStyle.blurple,
                    emoji=None,
                    disabled=True,
                    button_type="first",
                    paginator=self,
                ),
                "hidden": True,
            },
            "prev": {
                "object": PaginatorButton(
                    label="<",
                    style=discord.ButtonStyle.green,
                    emoji=None,
                    disabled=True,
                    button_type="prev",
                    paginator=self,
                ),
                "hidden": True,
            },
            "page_indicator": {
                "object": discord.ui.Button(
                    label=f"{self.current_page + 1}/{self.page_count + 1}",
                    style=discord.ButtonStyle.gray,
                    disabled=True,
                    row=4,
                ),
                "hidden": False,
            },
            "next": {
                "object": PaginatorButton(
                    label=">",
                    style=discord.ButtonStyle.green,
                    emoji=None,
                    disabled=True,
                    button_type="next",
                    paginator=self,
                ),
                "hidden": True,
            },
            "last": {
                "object": PaginatorButton(
                    label=">>",
                    style=discord.ButtonStyle.blurple,
                    emoji=None,
                    disabled=True,
                    button_type="last",
                    paginator=self,
                ),
                "hidden": True,
            },
        }
        self.update_buttons()

        self.usercheck = author_check
        self.user = None

    async def on_timeout(self) -> None:
        """Disables all buttons when the view times out."""
        if self.disable_on_timeout:
            for item in self.children:
                item.disabled = True
            await self.message.edit(view=self)

    async def goto_page(self, interaction: discord.Interaction, page_number=0) -> None:
        """Updates the interaction response message to show the specified page number.

        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction that invoked the paginator.
        page_number: :class:`int`
            The page to display.

            .. note::

                Page numbers are zero-indexed when referenced internally, but appear as one-indexed when shown to the user.
        """
        self.update_buttons()
        page = self.pages[page_number]
        await interaction.response.edit_message(
            content=page if isinstance(page, str) else None, embed=page if isinstance(page, discord.Embed) else None, view=self
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.usercheck:
            return self.user == interaction.user
        return True

    def customize_button(
        self, button_name: str = None, button_label: str = None, button_emoji=None, button_style: discord.ButtonStyle = discord.ButtonStyle.gray
    ) -> PaginatorButton:
        """Allows you to easily customize the various pagination buttons.

        Parameters
        ----------
        button_name: :class:`str`
            The name of the button to customize.
            Must be one of ``first``, ``prev``, ``next``, or ``last``.
        button_label: :class:`str`
            The label to display on the button.
        button_emoji:
            The emoji to display on the button.
        button_style: :class:`~discord.ButtonStyle`
            The ButtonStyle to use for the button.

        Returns
        -------
        :class:`~PaginatorButton`
            The button that was customized.
        """

        if button_name not in self.buttons.keys():
            raise ValueError(f"no button named {button_name} was found in this view.")
        button: discord.ext.pages.PaginatorButton = self.buttons[button_name]["object"]
        button.label = button_label
        button.emoji = button_emoji
        button.style = button_style
        return button
    
    def update_message(self, mes):
        self.messages[self.current_page] = mes
        for child in self.views[self.current_page].children:
            child.disabled=True
        for child_ind in self.custom_view.children[:-5]:
            self.custom_view.children.pop(child_ind)
            self.children.pop(child_ind)

        self.done[self.current_page] = True
    
    def all_done(self):
        return all(self.done)

    def enable_confirm(self):
        if self.error['type'] in {'tie'} and (self.selected_values!=len(self.error['player_names']) or len(self.error['placements']) > len(set(self.selected_values))):
            return

        for child in self.custom_view.children:
            child.disabled=False

    def update_attrs(self, view):
        self.bot = view.bot
        self.prefix = view.prefix
        self.error = view.error
        self.lounge = view.lounge
        self.index = view.index
        self.selected_values = view.selected_values

    def update_buttons(self) -> Dict:
        """Updates the display state of the buttons (disabled/hidden)

        Returns
        -------
        Dict[:class:`str`, Dict[:class:`str`, Union[:class:`~PaginatorButton`, :class:`bool`]]]
            The dictionary of buttons that were updated.
        """
        for key, button in self.buttons.items():
            if key == "first":
                if self.current_page <= 1:
                    button["hidden"] = True
                elif self.current_page >= 1:
                    button["hidden"] = False
            elif key == "last":
                if self.current_page >= self.page_count - 1:
                    button["hidden"] = True
                if self.current_page < self.page_count - 1:
                    button["hidden"] = False
            elif key == "next":
                if self.current_page == self.page_count:
                    button["hidden"] = True
                elif self.current_page < self.page_count:
                    button["hidden"] = False
            elif key == "prev":
                if self.current_page <= 0:
                    button["hidden"] = True
                elif self.current_page >= 0:
                    button["hidden"] = False
        self.clear_items()

        self.custom_view = self.views[self.current_page]
        self.update_attrs(self.custom_view)
        if self.custom_view:
            for item in self.custom_view.children:
                self.add_item(item)

        if self.show_indicator:
            self.buttons["page_indicator"]["object"].label = f"{self.current_page + 1}/{self.page_count + 1}"
        for key, button in self.buttons.items():
            if key != "page_indicator":
                if button["hidden"]:
                    button["object"].disabled = True
                    if self.show_disabled:
                        self.add_item(button["object"])
                else:
                    button["object"].disabled = False
                    self.add_item(button["object"])
            elif self.show_indicator:
                self.add_item(button["object"])

        return self.buttons
    
    async def send(self, messageable: abc.Messageable, ephemeral: bool = False) -> Union[discord.Message, discord.WebhookMessage]:
        """Sends a message with the paginated items.


        Parameters
        ------------
        messageable: :class:`discord.abc.Messageable`
            The messageable channel to send to.
        ephemeral: :class:`bool`
            Choose whether the message is ephemeral or not. Only works with slash commands.

        Returns
        --------
        Union[:class:`~discord.Message`, :class:`~discord.WebhookMessage`]
            The message that was sent with the paginator.
        """
        if isinstance(messageable, discord.Message) or hasattr(messageable, 'proxy'):
            self.user = messageable.author
            messageable = messageable.channel

        if not isinstance(messageable, abc.Messageable):
            raise TypeError("messageable should be a subclass of abc.Messageable")

        page = self.pages[0]

        if isinstance(messageable, (ApplicationContext, Context)):
            self.user = messageable.author

        if isinstance(messageable, ApplicationContext):
            msg = await messageable.respond(
                content=page if isinstance(page, str) else None,
                embed=page if isinstance(page, discord.Embed) else None,
                view=self,
                ephemeral=ephemeral,
            )

        else:
            msg = await messageable.send(
                content=page if isinstance(page, str) else None,
                embed=page if isinstance(page, discord.Embed) else None,
                view=self,
            )
        if isinstance(msg, (discord.WebhookMessage, discord.Message)):
            self.message = msg
        elif isinstance(msg, discord.Interaction):
            self.message = await msg.original_message()

        return self.message

    async def respond(self, interaction: discord.Interaction, ephemeral: bool = False):
        """Sends an interaction response or followup with the paginated items.


        Parameters
        ------------
        interaction: :class:`discord.Interaction`
            The interaction associated with this response.
        ephemeral: :class:`bool`
            Choose whether the message is ephemeral or not.

        Returns
        --------
        :class:`~discord.Interaction`
            The message sent with the paginator.
        """
        page = self.pages[0]
        self.user = interaction.user

        if interaction.response.is_done():
            msg = await interaction.followup.send(
                content=page if isinstance(page, str) else None, embed=page if isinstance(page, discord.Embed) else None, view=self, ephemeral=ephemeral
            )

        else:
            msg = await interaction.response.send_message(
                content=page if isinstance(page, str) else None, embed=page if isinstance(page, discord.Embed) else None, view=self, ephemeral=ephemeral
            )
        if isinstance(msg, (discord.WebhookMessage, discord.Message)):
            self.message = msg
        elif isinstance(msg, discord.Interaction):
            self.message = await msg.original_message()
        return self.message