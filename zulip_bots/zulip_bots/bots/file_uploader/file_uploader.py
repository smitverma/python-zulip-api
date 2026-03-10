import os
from pathlib import Path
from typing import Dict

from zulip_bots.lib import AbstractBotHandler


class FileUploaderHandler:
    def usage(self) -> str:
        return (
            "This interactive bot is used to upload files (such as images) to the Zulip server:"
            "\n- @uploader <local_file_path> : Upload a file, where <local_file_path> is the path to the file"
            "\n- @uploader help : Display help message"
        )

    def initialize(self, bot_handler: AbstractBotHandler) -> None:
        config = bot_handler.get_config_info("file_uploader", optional=True)
        upload_dir = config.get("upload_directory") if config else None
        if upload_dir:
            self.upload_directory = Path(upload_dir).resolve()
        else:
            self.upload_directory = Path.cwd()

    def handle_message(self, message: Dict[str, str], bot_handler: AbstractBotHandler) -> None:
        help_str = (
            "Use this bot with any of the following commands:"
            "\n* `@uploader <local_file_path>` : Upload a file, where `<local_file_path>` is the path to the file"
            "\n* `@uploader help` : Display help message"
        )

        content = message["content"].strip()
        if content == "help":
            bot_handler.send_reply(message, help_str)
            return

        path = Path(os.path.expanduser(content)).resolve()
        # resolve() follows symlinks, so the relative_to check is performed on the
        # real filesystem path, preventing symlink-based traversal attacks.
        try:
            path.relative_to(self.upload_directory)
        except ValueError:
            bot_handler.send_reply(
                message,
                "Access denied: file path must be within the configured upload directory.",
            )
            return

        if not path.is_file():
            bot_handler.send_reply(message, f"File `{content}` not found")
            return

        upload = bot_handler.upload_file_from_path(str(path))
        if upload["result"] != "success":
            msg = upload["msg"]
            bot_handler.send_reply(message, f"Failed to upload `{path}` file: {msg}")
            return

        uploaded_file_reply = "[{}]({})".format(path.name, upload["uri"])
        bot_handler.send_reply(message, uploaded_file_reply)


handler_class = FileUploaderHandler
