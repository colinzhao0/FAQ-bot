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
        removals = len(knowledge_base['questions'])
        knowledge_base["questions"] = []
        save_knowledge_base('knowledge_base.json',knowledge_base)
        await ctx.respond(f"Knowledge base cleared({removals} entries removed)!")

    except:
        await ctx.respond("Something went wrong!")

class PageToggle(discord.ui.View): 
    def __init__(self, knowledge_base, page_num=0):
        super().__init__()
        self.knowledge_base = knowledge_base
        self.page_num = page_num  # Tracks the current page number

    async def update_embed(self, interaction):
        # Create an embed for the current page of the knowledge base
        embed = discord.Embed(
            title="FAQ-Bot Knowledgebase",
            color=discord.Colour.blurple(),
        )

        # Determine the range of questions to display on the current page
        start = self.page_num * 10
        end = min((self.page_num + 1) * 10, len(self.knowledge_base["questions"]))
        for q in self.knowledge_base["questions"][start:end]:
            embed.add_field(name=q["question"], value=q["answer"], inline=False)

        # Add footer with page information
        embed.set_footer(text=f"Page {self.page_num + 1}/{(len(self.knowledge_base['questions']) - 1) // 10 + 1}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⬅️")
    async def left_button_callback(self, button, interaction):
        # Navigate to the previous page if not on the first page
        if self.page_num > 0:
            self.page_num -= 1
            await self.update_embed(interaction)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="➡️")
    async def right_button_callback(self, button, interaction):
        # Navigate to the next page if there are more pages
        if (self.page_num + 1) * 10 < len(self.knowledge_base["questions"]):
            self.page_num += 1
            await self.update_embed(interaction)

@bot.slash_command(name="knowledgebase", description="View the knowledge base", guild_ids=[1354165869437255871])
async def knowledgebase(ctx):
    await ctx.channel.trigger_typing()
    try:
        if len(knowledge_base["questions"]) > 0:
            # Initialize the pagination view
            view = PageToggle(knowledge_base)
            
            # Create the initial embed for the first page
            embed = discord.Embed(
                title="FAQ-Bot Knowledgebase",
                color=discord.Colour.blurple(),
            )
            start = 0
            end = min(10, len(knowledge_base["questions"]))
            for q in knowledge_base["questions"][start:end]:
                embed.add_field(name=q["question"], value=q["answer"], inline=False)
            embed.set_footer(text=f"Page 1/{(len(knowledge_base['questions']) - 1) // 10 + 1}")
            
            # Send the embed with the pagination buttons
            await ctx.respond("Here is my knowledge base:", embed=embed, view=view)
        else:
            # Respond if the knowledge base is empty
            await ctx.respond("No questions in the knowledge base!")
    except Exception as e:
        # Handle any unexpected errors
        print(f"Error: {e}")
        await ctx.respond("Something went wrong!")

# Load the knowledge base from the JSON file
knowledge_base: dict = load_knowledge_base('knowledge_base.json')

# Run the bot using the token from the environment variables
bot.run(os.getenv('DISCORD_TOKEN'))
