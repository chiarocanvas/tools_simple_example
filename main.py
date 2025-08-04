from  openai import  OpenAI
import json  
from typing import Dict , Any, Optional
import requests
from  ddgs import DDGS
from typing import Dict, Any, Optional
import smtplib
from email.message import EmailMessage
import getpass

def crypto_tool(coin_id:str) -> Dict[str, Any]:
        print(f"получаем цену {coin_id}")
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url)
        return response.json()


def detect_smtp_server(email: str) -> Optional[Dict[str, Any]]:
    """Определяет SMTP-сервер по домену почты."""
    domain = email.split("@")[-1].lower()
    smtp_servers = {
        "gmail.com": {"server": "smtp.gmail.com", "port": 465, "ssl": True},
        "mail.ru": {"server": "smtp.mail.ru", "port": 465, "ssl": True},
        "yandex.ru": {"server": "smtp.yandex.ru", "port": 465, "ssl": True},
    }
    return smtp_servers.get(domain)

def email_tool(
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
    password: Optional[str] = None,
) -> Dict[str, Any]:
    smtp_config = detect_smtp_server(from_email)
    if not smtp_config:
        return {
            "status": "error",
            "message": f"Неизвестный почтовый домен в {from_email}. "
                       f"Поддерживаются: Gmail, Mail.ru, Яндекс",
        }

    if password is None:
        password = getpass.getpass(f"Введите пароль для {from_email}: ")

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email


    if smtp_config["ssl"]:
        with smtplib.SMTP_SSL(smtp_config["server"], smtp_config["port"]) as server:
            server.login(from_email, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(smtp_config["server"], smtp_config["port"]) as server:
            server.starttls() 
            server.login(from_email, password)
            server.send_message(msg)

    return {"status": "success", "message": "Письмо успешно отправлено!"}


def search_tool(
        query:str,
        num_resulst:int = 5
        ):
    


    try:    
        not_text_urls = ['youtube.com']
        for  url in  not_text_urls:
            query+=f" -site:{url}"

        result = DDGS().text(query, max_results=num_resulst)
        return  result[0]['body']
    except Exception as e:
        error_msg = ("❌ Failed to fetch results from the web", str(e))
        print(error_msg)

client = OpenAI(
    base_url='http://127.0.0.1:1234/v1',
    api_key="lm-stydio",  
)

available_functions = {
    "email_tool": email_tool,
    "search_tool": search_tool,
    "crypto_tool": crypto_tool,
}
messages = [
        {
            "role": "system",
            "content": """Ты персональный ассистент, который ДОЛЖЕН использовать функции для ответа. 
Всегда вызывай функции вместо текстовых ответов. Инструкции:
1. Для криптовалют - используй crypto_tool
2. Для поиска - используй search_tool
3. Для писем - используй email_tool
Если запрос неясен - уточни, но не давай текстовых ответов!""",
        },
    ]

with  open('tool_conf.json') as tool:
    tools_list = json.load(tool)
    print(tools_list)
def execute_tool(tool_name: str, params: Dict[str, Any]) -> Any:
    if tool_name not in available_functions:
            return f"Ошибка: инструмент {tool_name} не найден"
        
    if tool_name == "email_tool":
            password = getpass.getpass(f"Введите пароль для {params['from_mail']}: ")
            params['password'] = password
        
    return available_functions[tool_name](**params)
def query_loop(messages):
    while True:
        response = client.chat.completions.create(
            model='ruadapt_qwen2.5_7b_ext_u48_instruct_gguf',
            messages=messages,
            tools=tools_list,
            temperature=0.7,
        )
        assistant_message = response.choices[0].message

        if assistant_message.tool_calls:
            messages.append(assistant_message)
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_result = execute_tool(function_name, function_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })
        else:
            messages.append(assistant_message)
            print(f"\n🤖: {assistant_message.content}\n")
            break


while  True:
    query = input("Слушаю:")
    messages.append({"role": "user", "content": query})
    query_loop(messages)

    