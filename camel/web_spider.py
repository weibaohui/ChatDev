import requests
from bs4 import BeautifulSoup
import openai
import wikipediaapi
import os

self_api_key = os.environ.get('OPENAI_API_KEY')
BASE_URL = os.environ.get('BASE_URL')

if BASE_URL:
    client = openai.OpenAI(
        api_key=self_api_key,
        base_url=BASE_URL,
    )
else:
    client = openai.OpenAI(
        api_key=self_api_key
    )


def get_baidu_baike_content(keyword):
    # design api by the baidubaike
    url = f'https://baike.baidu.com/item/{keyword}'
    # post request
    response = requests.get(url)

    # Beautiful Soup part for the html content
    soup = BeautifulSoup(response.content, 'html.parser')
    # find the main content in the page
    # main_content = soup.find('div', class_='lemma-summary')
    main_content = soup.contents[-1].contents[0].contents[4].attrs['content']
    # find the target content
    # content_text = main_content.get_text().strip()
    return main_content


def get_wiki_content(keyword):
    #  Wikipedia API ready
    wiki_wiki = wikipediaapi.Wikipedia('MyProjectName (merlin@example.com)', 'en')
    #the topic content which you want to spider
    search_topic = keyword
    # get the page content
    page_py = wiki_wiki.page(search_topic)
    # check the existence of the content in the page
    if page_py.exists():
        print("Page - Title:", page_py.title)
        print("Page - Summary:", page_py.summary)
    else:
        print("Page not found.")
    return page_py.summary


def modal_trans(task_dsp):
    try:
        task_in = "'" + task_dsp + \
                  "'只要给我关于这句话的最重要的关键词而不解释它，你的答案就应该只有一个关键词。"
        response_text = _get_openai_summary(task_in)
        print(f"提取关键词: {response_text}")
        spider_content = get_baidu_baike_content(response_text)
        # time.sleep(1)
        task_in = "'" + spider_content + \
                  "',总结这一段文本并返回关键信息。"
        result = _get_openai_summary(task_in)
        print(f"总结返回文本: {response_text}")
        print("web spider content:", result)
    except:
        result = ''
        print("the content is none")
    return result


def _get_openai_summary(task_in):
    messages = [{"role": "user", "content": task_in}]
    response = client.chat.completions.create(messages=messages,
                                              model="gpt-3.5-turbo-16k",
                                              temperature=0.2,
                                              top_p=1.0,
                                              n=1,
                                              stream=False,
                                              frequency_penalty=0.0,
                                              presence_penalty=0.0,
                                              logit_bias={})
    result = response.choices[0].message.content
    return result


if "__main__" == __name__:
    get_baidu_baike_content("北京")