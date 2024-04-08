import difflib
import os
import re
import subprocess

from chatdev.utils import log_visualize


class Codes:
    def __init__(self, generated_content=""):
        self.directory: str = None
        self.version: float = 0.0
        self.generated_content: str = generated_content
        self.codebooks = {}

        def extract_filename_from_line(lines):
            file_name = ""
            for candidate in re.finditer(r"(\w+\.\w+)", lines, re.DOTALL):
                file_name = candidate.group()
                file_name = file_name.lower()
            return file_name

        def extract_filename_from_code(code):
            file_name = ""
            regex_extract = r"class (\S+?):\n"
            matches_extract = re.finditer(regex_extract, code, re.DOTALL)
            for match_extract in matches_extract:
                file_name = match_extract.group(1)
            file_name = file_name.lower().split("(")[0] + ".py"
            return file_name

        if generated_content != "":
            regex = r"(.+?)\n```.*?\n(.*?)```"
            matches = re.finditer(regex, self.generated_content, re.DOTALL)
            for match in matches:
                code = match.group(2)
                if "CODE" in code:
                    continue
                group1 = match.group(1)
                filename = extract_filename_from_line(group1)
                if "__main__" in code:
                    filename = "main.py"
                if filename == "":  # post-processing
                    filename = extract_filename_from_code(code)
                assert filename != ""
                if filename is not None and code is not None and len(filename) > 0 and len(code) > 0:
                    self.codebooks[filename] = self._format_code(code)

    def _format_code(self, code):
        code = "\n".join([line for line in code.split("\n") if len(line.strip()) > 0])
        return code

    def _update_codes(self, generated_content):
        new_codes = Codes(generated_content)
        differ = difflib.Differ()
        for key in new_codes.codebooks.keys():
            if key not in self.codebooks.keys() or self.codebooks[key] != new_codes.codebooks[key]:
                update_codes_content = "**[更新代码]**\n\n"
                update_codes_content += f"更新 {key}\n"
                old_codes_content = self.codebooks[key] if key in self.codebooks.keys() else "# None"
                new_codes_content = new_codes.codebooks[key]

                lines_old = old_codes_content.splitlines()
                lines_new = new_codes_content.splitlines()

                unified_diff = difflib.unified_diff(lines_old, lines_new, lineterm='', fromfile='Old', tofile='New')
                unified_diff = '\n'.join(unified_diff)
                update_codes_content = update_codes_content + "\n\n" + """```
'''

'''\n""" + unified_diff + "\n```"

                log_visualize(update_codes_content)
                self.codebooks[key] = new_codes.codebooks[key]

    def _rewrite_codes(self, git_management, phase_info=None) -> None:
        directory = self.directory
        rewrite_codes_content = "**[重写代码]**\n\n"
        if os.path.exists(directory) and len(os.listdir(directory)) > 0:
            self.version += 1.0
        if not os.path.exists(directory):
            os.mkdir(self.directory)
            rewrite_codes_content += f"创建文件夹{directory} \n"

        for filename in self.codebooks.keys():
            filepath = os.path.join(directory, filename)
            with open(filepath, "w", encoding="utf-8") as writer:
                writer.write(self.codebooks[filename])
                rewrite_codes_content += "写入文件" + os.path.join(directory, filename) + "\n"

        if git_management:
            if not phase_info:
                phase_info = ""
            log_git_info = "**[运行 Git 命令]**\n\n"
            if self.version == 1.0:
                os.system(f"cd {self.directory}; git init")
                log_git_info += f"cd {self.directory}; git init\n"
            os.system(f"cd {self.directory}; git add .")
            log_git_info += f"cd {self.directory}; git add .\n"

            # check if there exist diff
            completed_process = subprocess.run(f"cd {self.directory}; git status", shell=True, text=True,
                                               stdout=subprocess.PIPE)
            if "nothing to commit" in completed_process.stdout:
                self.version -= 1.0
                return

            os.system(f"cd {self.directory}; git commit -m \"v{str(self.version) + ' ' + phase_info}\"")
            log_git_info += f"cd {self.directory}; git commit -m \"v{str(self.version) + ' ' + phase_info}\"\n"
            if self.version == 1.0:
                os.system(
                    f"cd {os.path.dirname(os.path.dirname(self.directory))}; "
                    f"git submodule add ./{'WareHouse/' + os.path.basename(self.directory)} {'WareHouse/' + os.path.basename(self.directory)}")
                log_git_info += f"cd {os.path.dirname(os.path.dirname(self.directory))}; git submodule add ./{'WareHouse/' + os.path.basename(self.directory)} {'WareHouse/' + os.path.basename(self.directory)}\n"
                log_visualize(rewrite_codes_content)
            log_visualize(log_git_info)

    def _get_codes(self) -> str:
        content = ""
        for filename in self.codebooks.keys():
            content += f"{filename}\n```{'python' if filename.endswith('.py') else filename.split('.')[-1]}\n{self.codebooks[filename]}\n```\n\n"
        return content

    def _load_from_hardware(self, directory) -> None:
        assert len([filename for filename in os.listdir(directory) if filename.endswith(".py")]) > 0
        for root, directories, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith(".py"):
                    code = open(os.path.join(directory, filename), "r", encoding="utf-8").read()
                    self.codebooks[filename] = self._format_code(code)
        log_visualize(f"从{directory}读取了{len(self.codebooks.keys())}个文件")
