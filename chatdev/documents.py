import re
import os
from colorama import Fore


class Documents:
    def __init__(self, generated_content="", parse=True, predefined_filename=None):
        self.directory: str = None
        self.generated_content = generated_content
        self.docbooks = {}

        if generated_content != "":
            if parse:
                regex = r"```\n(.*?)```"
                matches = re.finditer(regex, self.generated_content, re.DOTALL)
                for match in matches:
                    filename = "requirements.txt"
                    doc = match.group(1)
                    self.docbooks[filename] = doc
            else:
                self.docbooks[predefined_filename] = self.generated_content

    def _update_docs(self, generated_content, parse=True, predefined_filename=""):
        new_docs = Documents(generated_content, parse, predefined_filename)
        for key in new_docs.docbooks.keys():
            if key not in self.docbooks.keys() or self.docbooks[key] != new_docs.docbooks[key]:
                print(f"{key} 已更新.")
                print(Fore.BLUE + f"------Old:\n{self.docbooks[key] if key in self.docbooks.keys() else '# None'}\n"
                                  f"------New:\n{new_docs.docbooks[key]}")
                self.docbooks[key] = new_docs.docbooks[key]

    def _rewrite_docs(self):
        directory = self.directory
        if not os.path.exists(directory):
            os.mkdir(directory)
            print(f"新建文件夹：{directory} .")
        for filename in self.docbooks.keys():
            with open(os.path.join(directory, filename), "w", encoding="utf-8") as writer:
                writer.write(self.docbooks[filename])
                print(os.path.join(directory, filename) + " 已更新.")

    def _get_docs(self):
        content = ""
        for filename in self.docbooks.keys():
            content += f"{filename}\n```\n{self.docbooks[filename]}\n```\n\n"
        return content
