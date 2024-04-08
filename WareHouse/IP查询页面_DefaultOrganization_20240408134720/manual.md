# IP地址信息查询程序使用手册

## 介绍

IP地址信息查询程序是一个用于查询IP地址信息的console程序。它使用了[ip-api.com](http://ip-api.com/json/{IP}?lang=zh-CN)提供的API来获取IP地址的详细信息，包括国家、地区、城市、ISP、组织等。

## 安装

要使用IP地址信息查询程序，您需要在Python环境中安装以下依赖项：

```
requests==2.25.1
```

您可以使用以下命令来安装依赖项：

```bash
pip install -r requirements.txt
```

## 如何使用

### 查询IP地址信息

要查询IP地址信息，请执行以下步骤：

1. 打开命令行终端。

2. 进入IP地址信息查询程序的目录。

3. 运行`main.py`文件。

4. 输入要查询的IP地址。

5. 按下回车键。

6. 程序将会输出IP地址的详细信息，包括国家、地区、城市、ISP、组织等。

```bash
Enter IP address: 123.45.67.89
IP Address Information:
IP: 123.45.67.89
Country: 中国
Region: 北京市
City: 北京
ISP: 中国电信
Organization: 中国电信
AS: AS9808 China Unicom Beijing Province Network
Latitude: 39.9042
Longitude: 116.4074
```

请注意，如果查询过程中出现错误，程序将会输出相应的错误信息。

## 注意事项

- 请确保您的计算机已连接到互联网。

- 请确保输入的IP地址格式正确。

- 请注意，由于API的限制，每个IP地址的查询频率有限制。

- 请遵守[ip-api.com](http://ip-api.com/)的使用条款和隐私政策。

以上是IP地址信息查询程序的使用手册。如果您有任何问题或疑问，请随时联系我们的技术支持团队。