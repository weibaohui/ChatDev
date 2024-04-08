import importlib
import json
import logging
import os
import shutil
import time
from datetime import datetime

from camel.agents import RolePlaying
from camel.configs import ChatGPTConfig
from camel.typing import TaskType, ModelType
from chatdev.chat_env import ChatEnv, ChatEnvConfig
from chatdev.statistics import get_info
from camel.web_spider import modal_trans
from chatdev.utils import log_visualize, now


def check_bool(s):
    return s.lower() == "true"


class ChatChain:

    def __init__(self,
                 config_path: str = None,
                 config_phase_path: str = None,
                 config_role_path: str = None,
                 task_prompt: str = None,
                 project_name: str = None,
                 org_name: str = None,
                 model_type: ModelType = ModelType.GPT_3_5_TURBO,
                 code_path: str = None) -> None:
        """

        Args:
            config_path: path to the ChatChainConfig.json
            config_phase_path: path to the PhaseConfig.json
            config_role_path: path to the RoleConfig.json
            task_prompt: the user input prompt for software
            project_name: the user input name for software
            org_name: the organization name of the human user
        """

        # load config file
        self.config_path = config_path
        self.config_phase_path = config_phase_path
        self.config_role_path = config_role_path
        self.project_name = project_name
        self.org_name = org_name
        self.model_type = model_type
        self.code_path = code_path

        with open(self.config_path, 'r', encoding="utf8") as file:
            self.config = json.load(file)
        with open(self.config_phase_path, 'r', encoding="utf8") as file:
            self.config_phase = json.load(file)
        with open(self.config_role_path, 'r', encoding="utf8") as file:
            self.config_role = json.load(file)

        # init chatchain config and recruitments
        self.chain = self.config["chain"]
        self.recruitments = self.config["recruitments"]
        self.web_spider = self.config["web_spider"]

        # init default max chat turn
        self.chat_turn_limit_default = 10

        # init ChatEnv
        self.chat_env_config = ChatEnvConfig(clear_structure=check_bool(self.config["clear_structure"]),
                                             gui_design=check_bool(self.config["gui_design"]),
                                             git_management=check_bool(self.config["git_management"]),
                                             incremental_develop=check_bool(self.config["incremental_develop"]),
                                             background_prompt=self.config["background_prompt"],
                                             with_memory=check_bool(self.config["with_memory"]))
                                             
        self.chat_env = ChatEnv(self.chat_env_config)

        # the user input prompt will be self-improved (if set "self_improve": "True" in ChatChainConfig.json)
        # the self-improvement is done in self.preprocess
        self.task_prompt_raw = task_prompt
        self.task_prompt = ""

        # init role prompts
        self.role_prompts = dict()
        for role in self.config_role:
            self.role_prompts[role] = "\n".join(self.config_role[role])

        # init log
        self.start_time, self.log_filepath = self.get_log_filepath()

        # init SimplePhase instances
        # import all used phases in PhaseConfig.json from chatdev.phase
        # note that in PhaseConfig.json there only exist SimplePhases
        # ComposedPhases are defined in ChatChainConfig.json and will be imported in self.execute_step
        self.compose_phase_module = importlib.import_module("chatdev.composed_phase")
        self.phase_module = importlib.import_module("chatdev.phase")
        self.phases = dict()
        for phase in self.config_phase:
            assistant_role_name = self.config_phase[phase]['assistant_role_name']
            user_role_name = self.config_phase[phase]['user_role_name']
            phase_prompt = "\n\n".join(self.config_phase[phase]['phase_prompt'])
            phase_class = getattr(self.phase_module, phase)
            phase_instance = phase_class(assistant_role_name=assistant_role_name,
                                         user_role_name=user_role_name,
                                         phase_prompt=phase_prompt,
                                         role_prompts=self.role_prompts,
                                         phase_name=phase,
                                         model_type=self.model_type,
                                         log_filepath=self.log_filepath)
            self.phases[phase] = phase_instance

    def make_recruitment(self):
        """
        recruit all employees
        Returns: None

        """
        for employee in self.recruitments:
            self.chat_env.recruit(agent_name=employee)

    def execute_step(self, phase_item: dict):
        """
        execute single phase in the chain
        Args:
            phase_item: single phase configuration in the ChatChainConfig.json

        Returns:

        """

        phase = phase_item['phase']
        phase_type = phase_item['phaseType']
        # For SimplePhase, just look it up from self.phases and conduct the "Phase.execute" method
        if phase_type == "SimplePhase":
            max_turn_step = phase_item['max_turn_step']
            need_reflect = check_bool(phase_item['need_reflect'])
            if phase in self.phases:
                self.chat_env = self.phases[phase].execute(self.chat_env,
                                                           self.chat_turn_limit_default if max_turn_step <= 0 else max_turn_step,
                                                           need_reflect)
            else:
                raise RuntimeError(f"Phase '{phase}' 在 chatdev.phase 没有实现")
        # For ComposedPhase, we create instance here then conduct the "ComposedPhase.execute" method
        elif phase_type == "ComposedPhase":
            cycle_num = phase_item['cycleNum']
            composition = phase_item['Composition']
            compose_phase_class = getattr(self.compose_phase_module, phase)
            if not compose_phase_class:
                raise RuntimeError(f"Phase '{phase}' 在 chatdev.compose_phase 中没有实现")
            compose_phase_instance = compose_phase_class(phase_name=phase,
                                                         cycle_num=cycle_num,
                                                         composition=composition,
                                                         config_phase=self.config_phase,
                                                         config_role=self.config_role,
                                                         model_type=self.model_type,
                                                         log_filepath=self.log_filepath)
            self.chat_env = compose_phase_instance.execute(self.chat_env)
        else:
            raise RuntimeError(f"PhaseType '{phase_type}' is not yet implemented.")

    def execute_chain(self):
        """
        execute the whole chain based on ChatChainConfig.json
        Returns: None

        """
        for phase_item in self.chain:
            self.execute_step(phase_item)

    def get_log_filepath(self):
        """
        get the log path (under the software path)
        Returns:
            start_time: time for starting making the software
            log_filepath: path to the log

        """
        start_time = now()
        filepath = os.path.dirname(__file__)
        # root = "/".join(filepath.split("/")[:-1])
        root = os.path.dirname(filepath)
        # directory = root + "/WareHouse/"
        directory = os.path.join(root, "WareHouse")
        log_filepath = os.path.join(directory,
                                    f"{'_'.join([self.project_name, self.org_name, start_time])}.log")
        return start_time, log_filepath

    def pre_processing(self):
        """
        remove useless files and log some global config settings
        Returns: None

        """
        filepath = os.path.dirname(__file__)
        root = os.path.dirname(filepath)
        directory = os.path.join(root, "WareHouse")

        if self.chat_env.config.clear_structure:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                # logs with error trials are left in WareHouse/
                if os.path.isfile(file_path) and not filename.endswith(".py") and not filename.endswith(".log"):
                    os.remove(file_path)
                    print(f"{file_path} 已删除.")

        software_path = os.path.join(directory, "_".join([self.project_name, self.org_name, self.start_time]))
        self.chat_env.set_directory(software_path)

        if self.chat_env.config.with_memory is True:
            self.chat_env.init_memory()

        # copy config files to software path
        shutil.copy(self.config_path, software_path)
        shutil.copy(self.config_phase_path, software_path)
        shutil.copy(self.config_role_path, software_path)

        # copy code files to software path in incremental_develop mode
        if check_bool(self.config["incremental_develop"]):
            for root, dirs, files in os.walk(self.code_path):
                relative_path = os.path.relpath(root, self.code_path)
                target_dir = os.path.join(software_path, 'base', relative_path)
                os.makedirs(target_dir, exist_ok=True)
                for file in files:
                    source_file = os.path.join(root, file)
                    target_file = os.path.join(target_dir, file)
                    shutil.copy2(source_file, target_file)
            self.chat_env._load_from_hardware(os.path.join(software_path, 'base'))

        # write task prompt to software
        with open(os.path.join(software_path, self.project_name + ".prompt"), "w") as f:
            f.write(self.task_prompt_raw)

        preprocess_msg = "**[处理中]**\n\n"
        chat_gpt_config = ChatGPTConfig()

        preprocess_msg += f"**ChatDev 启动时间** ({self.start_time})\n\n"
        preprocess_msg += f"**时间戳**: {self.start_time}\n\n"
        preprocess_msg += f"**ChatChinConfig路径**: {self.config_path}\n\n"
        preprocess_msg += f"**PhaseConfig路径**: {self.config_phase_path}\n\n"
        preprocess_msg += f"**RoleConfig路径**: {self.config_role_path}\n\n"
        preprocess_msg += f"**任务提示**: {self.task_prompt_raw}\n\n"
        preprocess_msg += f"**项目名称**: {self.project_name}\n\n"
        preprocess_msg += f"**运行日志路径**: {self.log_filepath}\n\n"
        preprocess_msg += f"**ChatDev配置**:\n{self.chat_env.config.__str__()}\n\n"
        preprocess_msg += f"**ChatGPT大模型配置**:\n{chat_gpt_config}\n\n"
        log_visualize(preprocess_msg)

        # init task prompt
        if check_bool(self.config['self_improve']):
            self.chat_env.env_dict['task_prompt'] = self.self_task_improve(self.task_prompt_raw)
        else:
            self.chat_env.env_dict['task_prompt'] = self.task_prompt_raw
        if check_bool(self.web_spider):
            self.chat_env.env_dict['task_description'] = modal_trans(self.task_prompt_raw)

    def post_processing(self):
        """
        summarize the production and move log files to the software directory
        Returns: None

        """

        self.chat_env.write_meta()
        filepath = os.path.dirname(__file__)
        root = os.path.dirname(filepath)

        if self.chat_env_config.git_management:
            log_git_info = "**[Git 信息]**\n\n"

            self.chat_env.codes.version += 1
            os.system(f"cd {self.chat_env.env_dict['directory']}; git add .")
            log_git_info += f"cd {self.chat_env.env_dict['directory']}; git add .\n"
            os.system(
                f"cd {self.chat_env.env_dict['directory']}; git commit -m \"v{self.chat_env.codes.version} Final "
                f"Version\"")
            log_git_info += (f"cd {self.chat_env.env_dict['directory']}; git commit -m \"v{self.chat_env.codes.version} "
                             f"Final Version\"\n")
            log_visualize(log_git_info)

            git_info = "**[Git Log]**\n\n"
            import subprocess

            # execute git log
            command = f"cd {self.chat_env.env_dict['directory']}; git log"
            completed_process = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE)

            if completed_process.returncode == 0:
                log_output = completed_process.stdout
            else:
                log_output = "Error when executing " + command

            git_info += log_output
            log_visualize(git_info)

        post_info = "**[Post Info]**\n\n"
        now_time = now()
        time_format = "%Y%m%d%H%M%S"
        datetime1 = datetime.strptime(self.start_time, time_format)
        datetime2 = datetime.strptime(now_time, time_format)
        duration = (datetime2 - datetime1).total_seconds()

        post_info += "软件信息: {}".format(
            get_info(self.chat_env.env_dict['directory'], self.log_filepath) + f"\n\n🕑**运行耗时**={duration:.2f}s\n\n")

        post_info += f"ChatDev 开始时间 ({self.start_time})" + "\n\n"
        post_info += f"ChatDev 完成时间 ({now_time})" + "\n\n"

        directory = self.chat_env.env_dict['directory']
        if self.chat_env.config.clear_structure:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isdir(file_path) and file_path.endswith("__pycache__"):
                    shutil.rmtree(file_path, ignore_errors=True)
                    post_info += f"{file_path} 已删除." + "\n\n"

        log_visualize(post_info)

        logging.shutdown()
        time.sleep(1)

        shutil.move(self.log_filepath,
                    os.path.join(root + "/WareHouse", "_".join([self.project_name, self.org_name, self.start_time]),
                                 os.path.basename(self.log_filepath)))

    # @staticmethod
    def self_task_improve(self, task_prompt):
        """
        ask agent to improve the user query prompt
        Args:
            task_prompt: original user query prompt

        Returns:
            revised_task_prompt: revised prompt from the prompt engineer agent

        """
        self_task_improve_prompt = """我会给你一个软件设计需求的简短描述，
请把它重写成一个详细的提示，可以让大语言模型知道如何根据这个提示让这个软件更好，
提示应该确保LLMs构建一个可以正确运行的软件，这是您需要考虑的最重要的部分。
请记住，修改后的提示不应超过 200 个单词，
这是简短的描述：\"{}\"。
如果修改后的提示是revised_version_of_the_description，
那么你应该以\"<INFO> revision_version_of_the_description\" 这样的格式返回消息，不要返回其他格式的消息。""".format(
            task_prompt)
        role_play_session = RolePlaying(
            assistant_role_name="提示词工程师",
            assistant_role_prompt="你是一名专业的提示词工程师，可以改进用户输入提示，使LLM更好地理解这些提示",
            user_role_prompt="你是一个希望使用LLM来构建软件的用户.",
            user_role_name="User",
            task_type=TaskType.CHATDEV,
            task_prompt="对用户的查询进行提示词优化工程",
            with_task_specify=False,
            model_type=self.model_type,
        )

        # log_visualize("System", role_play_session.assistant_sys_msg)
        # log_visualize("System", role_play_session.user_sys_msg)

        _, input_user_msg = role_play_session.init_chat(None, None, self_task_improve_prompt)
        assistant_response, user_response = role_play_session.step(input_user_msg, True)
        revised_task_prompt = assistant_response.msg.content.split("<INFO>")[-1].lower().strip()
        log_visualize(role_play_session.assistant_agent.role_name, assistant_response.msg.content)
        log_visualize(
            f"**[任务提示自我改进]**\n**原始提示词**: {task_prompt}\n**改进后提示词**: {revised_task_prompt}")
        return revised_task_prompt
