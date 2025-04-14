import discord, json, os
from discord import Option
from difflib import get_close_matches
from dotenv import load_dotenv

load_dotenv() # load all the variables from the env file
bot = discord.Bot()

#knowledge base functions
def load_knowledge_base(file_path:str) -> dict:
    with open(file_path,'r') as file:
        data:dict=json.load(file)
    return data

def save_knowledge_base(file_path:str,data:dict):
    with open(file_path,'w') as file:
        json.dump(data,file,indent=2)

def find_best_match(user_question:str,questions:list[str]) -> str|None:
    matches:list=get_close_matches(user_question,questions,n=1,cutoff=0.4)
    return matches[0] if matches else None

def get_answer_for_question(question:str,knowledge_base:dict) -> str|None:
    for q in knowledge_base["questions"]:
        if q["question"]==question:
            return q["answer"]


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.slash_command(name="ask", description="Ask the bot a question!", guild_ids=[1354165869437255871])
async def ask(ctx, question: str=discord.Option(str, description="What do you want to ask?", required=True)):
    await ctx.channel.trigger_typing()
    answer = ""
    try:
        best_match:str|None=find_best_match(question,[q['question'] for q in knowledge_base['questions']])
        if best_match:
            answer:str = get_answer_for_question(best_match,knowledge_base) 
            await ctx.respond(f"**Question**: {question} \n**Answer**: {answer}")
        else:
            await ctx.respond(f"**Question**: {question} \nI haven't been trained on this yet!")

    except:
        await ctx.respond("Something went wrong!")

#if question is blank, train last asked question
@bot.slash_command(name="train", description="Teach the bot! (Add new questions)", guild_ids=[1354165869437255871])
async def train(ctx, question: str = discord.Option(str, description="Question", required=True), answer: str = discord.Option(str, description="Answer", required=True)):
    await ctx.channel.trigger_typing()
    try:
        best_match:str|None=find_best_match(question,[q['question'] for q in knowledge_base['questions']])
        knowledge_base["questions"].append({"question":question,"answer":answer})
        save_knowledge_base('knowledge_base.json',knowledge_base)
        await ctx.respond(f"**Added:**\n**Question**: {question} \n**Answer**: {answer}")

    except:
        await ctx.respond("Something went wrong!")

@bot.slash_command(name="undo", description="Remove the last question from the knowledge base", guild_ids=[1354165869437255871])
async def undo(ctx):
    await ctx.channel.trigger_typing()
    try:
        if len(knowledge_base["questions"])>0:
            last_question = knowledge_base["questions"].pop()
            save_knowledge_base('knowledge_base.json',knowledge_base)
            await ctx.respond(f"**Removed:**\n**Question**: {last_question['question']} \n**Answer**: {last_question['answer']}")
        else:
            await ctx.respond("No questions to remove!")

    except:
        await ctx.respond("Something went wrong!")

@bot.slash_command(name="clear", description="Clear the knowledge base", guild_ids=[1354165869437255871])
async def clear(ctx):
    await ctx.channel.trigger_typing()
    try:
        knowledge_base["questions"] = []
        save_knowledge_base('knowledge_base.json',knowledge_base)
        await ctx.respond(f"Knowledge base cleared({len(knowledge_base["questions"])} entries removed)!")

    except:
        await ctx.respond("Something went wrong!")

class PageToggle(discord.ui.View): 
    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⬅️") 
    async def left_button_callback(self, button, interaction):
        await interaction.response.send_message("You clicked the left button!") 
        
        if pageNum - 1 > 0:
            pageNum -=1 

            start = pageNum*10
            end = min((KBSize*10), (pageNum+1)*10-1)

            for q in knowledge_base["questions"][start:end]:
                KBEmbed.add_field(name=q["question"], value=q["answer"], inline=False)

            KBEmbed.set_footer(text=f"Page {pageNum+1}/{(len(knowledge_base['questions']) - 1) // 10 + 1}")

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="➡️") 
    async def right_button_callback(self, button, interaction):
        await interaction.response.send_message("You clicked the right button!") 

        if pageNum + 1 <= KBSize/10:
            pageNum +=1 

            start = pageNum*10
            end = min((KBSize*10), (pageNum+1)*10-1)

            for q in knowledge_base["questions"][start:end]:
                KBEmbed.add_field(name=q["question"], value=q["answer"], inline=False)

            KBEmbed.set_footer(text=f"Page {pageNum+1}/{(len(knowledge_base['questions']) - 1) // 10 + 1}")


@bot.slash_command(name="knowledgebase", description="View the knowledge base", guild_ids=[1354165869437255871])
async def knowledgebase(ctx):
    await ctx.channel.trigger_typing()
    KBSize = len(knowledge_base["questions"])
    try:
        if len(knowledge_base["questions"])>0:
            start = pageNum*10
            end = min((KBSize*10), (pageNum+1)*10-1)

            for q in knowledge_base["questions"][start:end]:
                KBEmbed.add_field(name=q["question"], value=q["answer"], inline=False)

            KBEmbed.set_footer(text=f"Page {pageNum+1}/{(len(knowledge_base['questions']) - 1) // 10 + 1}")

            await ctx.respond(f"Here is my knowledgebase: ", embed=KBEmbed, view=PageToggle())
        else:
            await ctx.respond("No questions in the knowledge base!")

    except Exception as e:
        print(f"Error: {e}")
        await ctx.respond("Something went wrong!")

pageNum= 0
KBsize = 0

KBEmbed = discord.Embed(
        title="FAQ-Bot Knowledgebase",
        color=discord.Colour.blurple(), 
        )

knowledge_base:dict=load_knowledge_base('knowledge_base.json')
KBsize = KBSize = len(knowledge_base["questions"])
bot.run(os.getenv('DISCORD_TOKEN')) # run the bot with the token
