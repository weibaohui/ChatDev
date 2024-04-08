import os
import re
import shutil
import signal
import subprocess
import time
from typing import Dict

import openai
import requests

from chatdev.codes import Codes
from chatdev.documents import Documents
from chatdev.roster import Roster
from chatdev.utils import log_visualize
from ecl.memory import Memory

try:
    from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
    from openai.types.chat.chat_completion_message import FunctionCall

    openai_new_api = True  # new openai api version
except ImportError:
    openai_new_api = False  # old openai api version


class ChatEnvConfig:
    def __init__(self, clear_structure,
                 gui_design,
                 git_management,
                 incremental_develop,
                 background_prompt,
                 with_memory):
        self.clear_structure = clear_structure  # Whether to clear non-software files in the WareHouse and cache files in generated software path
        self.gui_design = gui_design  # Encourage ChatDev generate software with GUI
        self.git_management = git_management  # Whether to use git to manage the creation and changes of generated software
        self.incremental_develop = incremental_develop  # Whether to use incremental develop on an existing project
        self.background_prompt = background_prompt  # background prompt that will be added to every inquiry to LLM
        self.with_memory = with_memory  # Wheter to use memroy in the interaction between agents

    def __str__(self):
        string = ""
        string += f"ChatEnvConfig.with_memory: {self.with_memory}\n"
        string += f"ChatEnvConfig.clear_structure: {self.clear_structure}\n"
        string += f"ChatEnvConfig.git_management: {self.git_management}\n"
        string += f"ChatEnvConfig.gui_design: {self.gui_design}\n"
        string += f"ChatEnvConfig.incremental_develop: {self.incremental_develop}\n"
        string += f"ChatEnvConfig.background_prompt: {self.background_prompt}\n"
        return string


class ChatEnv:
    def __init__(self, chat_env_config: ChatEnvConfig):
        self.config = chat_env_config
        self.roster: Roster = Roster()
        self.codes: Codes = Codes()
        self.memory: Memory = Memory()
        self.proposed_images: Dict[str, str] = {}
        self.incorporated_images: Dict[str, str] = {}
        self.requirements: Documents = Documents()
        self.manuals: Documents = Documents()
        self.env_dict = {
            "directory": "",
            "task_prompt": "",
            "task_description": "",
            "modality": "",
            "ideas": "",
            "language": "",
            "review_comments": "",
            "error_summary": "",
            "test_reports": ""
        }

    @staticmethod
    def fix_module_not_found_error(test_reports):
        if "ModuleNotFoundError" in test_reports:
            for match in re.finditer(r"No module named '(\S+)'", test_reports, re.DOTALL):
                module = match.group(1)
                subprocess.Popen(f"pip install {module}", shell=True).wait()
                log_visualize(f"**[CMD Execute]**\n\n[CMD] pip install {module}")

    def set_directory(self, directory):
        assert len(self.env_dict['directory']) == 0
        self.env_dict['directory'] = directory
        self.codes.directory = directory
        self.requirements.directory = directory
        self.manuals.directory = directory

        if os.path.exists(self.env_dict['directory']) and len(os.listdir(directory)) > 0:
            new_directory = f"{directory}.{time.strftime('%Y%m%d%H%M%S', time.localtime())}"
            shutil.copytree(directory, new_directory)
            print(f"将{directory}复制到{new_directory}")
        if os.path.exists(self.env_dict['directory']):
            shutil.rmtree(self.env_dict['directory'])
            os.mkdir(self.env_dict['directory'])
            print(f"新建文件夹{directory}")
        else:
            os.mkdir(self.env_dict['directory'])

    def init_memory(self):
        self.memory.id_enabled = True
        self.memory.directory = os.path.join(os.getcwd(), "ecl", "memory")
        if not os.path.exists(self.memory.directory):
            os.mkdir(self.memory.directory)
        self.memory.upload()

    def exist_bugs(self) -> tuple[bool, str]:
        directory = self.env_dict['directory']

        success_info = "软件运行正常，没有报错."
        try:

            # check if we are on windows or linux
            if os.name == 'nt':
                command = f"cd {directory} && dir && python main.py"
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                command = f'cd {directory}; ls -l; python3 main.py;'
                process = subprocess.Popen(command,
                                           shell=True,
                                           preexec_fn=os.setsid,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE
                                           )
            time.sleep(3)
            return_code = process.returncode
            # Check if the software is still running
            if process.poll() is None:
                if "killpg" in dir(os):
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    os.kill(process.pid, signal.SIGTERM)
                    if process.poll() is None:
                        os.kill(process.pid, signal.CTRL_BREAK_EVENT)

            if return_code == 0:
                return False, success_info
            else:
                error_output = process.stderr.read().decode('utf-8')
                if error_output:
                    if "Traceback".lower() in error_output.lower():
                        errs = error_output.replace(directory + "/", "")
                        return True, errs
                else:
                    return False, success_info
        except subprocess.CalledProcessError as e:
            return True, f"错误: {e}"
        except Exception as ex:
            return True, f"发生错误: {ex}"

        return False, success_info

    def recruit(self, agent_name: str):
        self.roster._recruit(agent_name)

    def exist_employee(self, agent_name: str) -> bool:
        return self.roster._exist_employee(agent_name)

    def print_employees(self):
        self.roster._print_employees()

    def update_codes(self, generated_content):
        self.codes._update_codes(generated_content)

    def rewrite_codes(self, phase_info=None) -> None:
        self.codes._rewrite_codes(self.config.git_management, phase_info)

    def get_codes(self) -> str:
        return self.codes._get_codes()

    def _load_from_hardware(self, directory) -> None:
        self.codes._load_from_hardware(directory)

    def _update_requirements(self, generated_content):
        self.requirements._update_docs(generated_content)

    def rewrite_requirements(self):
        self.requirements._rewrite_docs()

    def get_requirements(self) -> str:
        return self.requirements._get_docs()

    def _update_manuals(self, generated_content):
        self.manuals._update_docs(generated_content, parse=False, predefined_filename="manual.md")

    def rewrite_manuals(self):
        self.manuals._rewrite_docs()

    def write_meta(self) -> None:
        directory = self.env_dict['directory']

        if not os.path.exists(directory):
            os.mkdir(directory)
            print(f"新建文件夹{directory}.")

        meta_filename = "meta.txt"
        with open(os.path.join(directory, meta_filename), "w", encoding="utf-8") as writer:
            writer.write(f"{'Task'}:\n{self.env_dict['task_prompt']}\n\n")
            writer.write(f"{'Config'}:\n{self.config.__str__()}\n\n")
            writer.write(f"{'Roster'}:\n{', '.join(self.roster.agents)}\n\n")
            writer.write(f"{'Modality'}:\n{self.env_dict['modality']}\n\n")
            writer.write(f"{'Ideas'}:\n{self.env_dict['ideas']}\n\n")
            writer.write(f"{'Language'}:\n{self.env_dict['language']}\n\n")
            writer.write(f"{'Code_Version'}:\n{self.codes.version}\n\n")
            writer.write(f"{'Proposed_images'}:\n{len(self.proposed_images.keys())}\n\n")
            writer.write(f"{'Incorporated_images'}:\n{len(self.incorporated_images.keys())}\n\n")
        print(f"写入{os.path.join(directory, meta_filename)}")

    def generate_images_from_codes(self):
        def download(img_url, file_name):
            r = requests.get(img_url)
            filepath = os.path.join(self.env_dict['directory'], file_name)
            if os.path.exists(filepath):
                os.remove(filepath)
            with open(filepath, "wb") as f:
                f.write(r.content)
                print(f"下载完成：{filepath}")

        regex = r"(\w+.png)"
        joined_codes = self.get_codes()
        matches = re.finditer(regex, joined_codes, re.DOTALL)
        # matched_images = {}
        for match in matches:
            filename = match.group(1).strip()
            if filename in self.proposed_images.keys():
                self.incorporated_images[filename] = self.proposed_images[filename]
            else:
                self.incorporated_images[filename] = filename.replace("_", " ")

        for filename in self.incorporated_images.keys():
            if not os.path.exists(os.path.join(self.env_dict['directory'], filename)):
                desc = self.incorporated_images[filename]
                if desc.endswith(".png"):
                    desc = desc.replace(".png", "")
                print(f"{filename}: {desc}")
                if openai_new_api:
                    response = openai.images.generate(
                        prompt=desc,
                        n=1,
                        size="256x256"
                    )
                    image_url = response.data[0].url
                else:
                    response = openai.Image.create(
                        prompt=desc,
                        n=1,
                        size="256x256"
                    )
                    image_url = response['data'][0]['url']
                download(image_url, filename)

    def get_proposed_images_from_message(self, messages):
        def download(img_url, file_name):
            r = requests.get(img_url)
            filepath = os.path.join(self.env_dict['directory'], file_name)
            if os.path.exists(filepath):
                os.remove(filepath)
            with open(filepath, "wb") as f:
                f.write(r.content)
                print(f"下载完成{filepath}")

        regex = r"(\w+.png):(.*?)\n"
        matches = re.finditer(regex, messages, re.DOTALL)
        images = {}
        for match in matches:
            filename = match.group(1).strip()
            desc = match.group(2).strip()
            images[filename] = desc

        if len(images.keys()) == 0:
            regex = r"(\w+.png)"
            matches = re.finditer(regex, messages, re.DOTALL)
            images = {}
            for match in matches:
                filename = match.group(1).strip()
                desc = " ".join(filename.replace(".png", "").split("_"))
                images[filename] = desc
                print(f"{filename}: {images[filename]}")

        for filename in images.keys():
            if not os.path.exists(os.path.join(self.env_dict['directory'], filename)):
                desc = images[filename]
                if desc.endswith(".png"):
                    desc = desc.replace(".png", "")
                print(f"{filename}: {desc}")

                if openai_new_api:
                    response = openai.images.generate(
                        prompt=desc,
                        n=1,
                        size="256x256"
                    )
                    image_url = response.data[0].url
                else:
                    response = openai.Image.create(
                        prompt=desc,
                        n=1,
                        size="256x256"
                    )
                    image_url = response['data'][0]['url']

                download(image_url, filename)

        return images
