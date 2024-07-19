from openai import OpenAI
import maricon
client = OpenAI(api_key=maricon.gptkey)

def generate_text(prompt):

    system_prompt = 'you are roleplaying as a corporate employee in an internal chat app. please generate a message based on the context provided.'

    full_prompt = [ {"role": "system", "content": f"{system_prompt}"},{"role": "user", "content": f"{prompt}"}]

    response = client.chat.completions.create(model="gpt-4o-mini",
    max_tokens=250,
    temperature=0.8,
    messages = full_prompt)

    print(response)
    
    generated_text = response.choices[0].message.content.strip()

    print(generated_text)

    return generated_text

#generate_text('you are Steve Smith, sending a message to Donald Lacrosse if he has finished reviewing the budget for the upcoming quarter.')