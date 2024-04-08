# 注意
1. 本仓库为官方仓库的中文版，相关提示词已经更新为中文，可视化演示界面也更新为中文了，欢迎大家体验。
2. 功能保持官方仓库，未做修改。
3. 在公司配置下，增加一个Smart文件夹，中文配置都在这个文件夹里，执行时请使用本配置

# Communicative Agents for Software Development

<p align="center">
  <img src='../misc/logo1.png' width=600>
</p>

<p align="center">
    【📚 <a href="../wiki.md">Wiki</a> | 🚀 <a href="../wiki.md#visualizer">Visualizer</a> | 👥 <a href="../Contribution.md">Community Built Software</a> | 🔧 <a href="../wiki.md#customization">Customization</a>】
</p>

## 📖 概述

- **ChatDev** 是一家**虚拟软件公司**，通过各种不同角色的**智能体**
  运营，包括执行官<img src='../visualizer/static/figures/ceo.png' height=20>，产品官<img src='../visualizer/static/figures/cpo.png' height=20>，技术官<img src='../visualizer/static/figures/cto.png' height=20>，程序员 <img src='../visualizer/static/figures/programmer.png' height=20>，审查员<img src='../visualizer/static/figures/reviewer.png' height=20>，测试员<img src='../visualizer/static/figures/tester.png' height=20>，设计师<img src='../visualizer/static/figures/designer.png' height=20> 等。这些智能体形成了一个多智能体组织结构，其使命是“通过编程改变数字世界”。ChatDev内的智能体通过参加专业的功能研讨会来
  **协作**，包括设计、编码、测试和文档编写等任务。
- ChatDev的主要目标是提供一个基于大型语言模型（LLM）的**易于使用**、**高度可定制**并且**可扩展**的框架，它是研究群体智能的理想场景。
  
## ⚡️ 快速开始

要开始使用，按照以下步骤操作：

1. **克隆GitHub存储库：** 首先，使用以下命令克隆存储库：

   ```
   git clone https://github.com/weibaohui/ChatDev.git
   ```

2. **设置Python环境：** 确保您具有3.9或更高版本的Python环境。您可以使用以下命令创建并激活环境，可以将`ChatDev_conda_env`
   替换为您喜欢的环境名称：

   ```
   conda create -n ChatDev_conda_env python=3.9 -y
   conda activate ChatDev_conda_env
   ```

3. **安装依赖项：** 进入`ChatDev`目录并运行以下命令来安装必要的依赖项：

   ```
   cd ChatDev
   pip3 install -r requirements.txt
   ```

4. **设置OpenAI API密钥：** 将您的OpenAI API密钥导出为环境变量。将`"your_OpenAI_API_key"`
   替换为您的实际API密钥。请注意，此环境变量是特定于会话的，因此如果打开新的终端会话，您需要重新设置它。
   在Unix/Linux系统上：

   ```
   export OPENAI_API_KEY="your_OpenAI_API_key"
   export BASE_URL="your_OpenAI_Server_Address/v1"
   ```

   在Windows系统上：

   ```
   $env:OPENAI_API_KEY="your_OpenAI_API_key"
   $env:BASE_URL="your_OpenAI_Server_Address/v1"
   ```

5. **构建您的软件：** 使用以下命令启动生成您的软件，将`[description_of_your_idea]`替换为您的想法描述，将`[project_name]`
   替换为您想要的项目名称：
   在Unix/Linux系统上：

   ```
   python3 run.py --task "[description_of_your_idea]" --name "[project_name]" --config "Smart"
   ```

   在Windows系统上：

   ```
   python run.py --task "[description_of_your_idea]" --name "[project_name]" --config "Smart"
   ```
6. **运行您的软件：** 生成后，您可以在`WareHouse`
   目录下的特定项目文件夹中找到您的软件，例如`project_name_DefaultOrganization_timestamp`。在该目录中运行以下命令来运行您的软件：
   在Unix/Linux系统上：

   ```
   cd WareHouse/project_name_DefaultOrganization_timestamp
   python3 main.py
   ```

   在Windows系统上：

   ```
   cd WareHouse/project_name_DefaultOrganization_timestamp
   python main.py
   ```
   