import re
import misaka as m


class LinkRenderer(m.HtmlRenderer):
    def preprocess(self, text):
        # Match /u/[username] & reformat it as a link
        fixed_content = re.sub(r"/u/([a-z0-9_-]{3,16})", r"[/u/\1](/u/\1)",
                               text, flags=re.IGNORECASE)
        # Match /c/[community_name] & reformat it as a link
        fixed_content = re.sub(r"/c/([a-z0-9_-]{4,32})", r"[/c/\1](/c/\1)",
                               fixed_content, flags=re.IGNORECASE)
        return fixed_content
