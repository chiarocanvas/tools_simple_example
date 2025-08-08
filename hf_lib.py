from smolagents import CodeAgent, FinalAnswerTool, InferenceClientModel, load_tool, tool
import datetime
import requests
import pytz
import yaml 




@tool 
def crypto_tool(coin_id:str) -> Dict[str, Any]:
        print(f"получаем цену {coin_id}")
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url)
        return response.json()


final_answer = FinalAnswerTool()
model = InferenceClientModel(
    max_tokens=2096,
    temperature=0.5,
    model_id='ruadapt_qwen2.5_7b_ext_u48_instruct_gguf',
    custom_role_conversions=None,
)
# add yourself  if  needed 
with open("prompts.yaml", 'r') as stream:
    prompt_templates = yaml.safe_load(stream)
    

agent = CodeAgent(
    model=model,
    tools=[final_answer,crypto_tool ], 
    max_steps=6,
    verbosity_level=1,
    grammar=None,
    planning_interval=None,
    name=None,
    description=None,
    prompt_templates=prompt_templates
)

GradioUI(agent).launch()