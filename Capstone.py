import random
from openai import OpenAI
import pygame
import time
import threading
import warnings
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from profanity_check import predict

# Setting global variables
avatars = {
    "Sleezy Sal": "dumpster",
    "Miami Mike": "cruise",
    "Logical Leo": "reasonable",
    "Eloquent Emma": "persuasive"
}

lawyers = list(avatars.keys())

judges = {
    "Judge Judy": ", she prefers factual arguments",
    "Judge Joe": ", he prefers emotional appeals",
    "Judge Jake": ", he prefers weird arguments",
    "Judge Jane": ", she prefers food related arguments"
}

cases = ["Theft", "Fraud", "Burglary", "Assault", "Disturbing the peace", "Crimes against humanity", "Tax evasion", "Murder"]

intro = "Welcome to Lawyer Up!\nIn this two-player game, you'll step into the shoes of a courtroom lawyer.\nChoose your legal champion and use special keywords to craft a powerful closing argument.\nImpress an AI judge and tip the scales of justice in your favor.\nRemember, each lawyer has a secret weapon, a unique keyword. Use your smarts to pick the right words and win the case.\nMay the best lawyer emerge victorious!"

now = datetime.now()

#Ignore the TTS warning
warnings.filterwarnings("ignore", category=DeprecationWarning)

#Function to pause the game and allow the audio to play fully
def wait_for_enter():
    """
    Waits for the user to press Enter.
    """
    input("Press Enter to continue once the dialogue finishes...")

# Function to generate a random court case
def generate_random_case():
    return random.choice(cases)

# Function to assign avatar and keyword
def assign_avatar_and_keyword(player_choice):
    return avatars[player_choice]

# Function to characterize the judge
def characterize_judge():
    judge_name = random.choice(list(judges.keys()))
    j_desc = 'Your judge is the honorable ' + judge_name + judges[judge_name]
    print(j_desc)
    return judge_name, judges[judge_name]

# Function to display the image options and capture user selection
def choose_lawyer():
    descriptions = ['1. Sleezy Sal, keyword: dumpster', '2. Miami Mike, keyword: cruise', '3. Logical Leo, keyword: reasonable', '4. Eloquent Emma, keyword: persuasive']
    print("Please choose one of the following lawyers by entering the corresponding number:")
    for description in descriptions:
        print(description)

    # Loop until a valid selection is made
    while True:
        user_choice = input("Your choice (1-4): ")
        if user_choice.isdigit():
            user_choice = int(user_choice)
            if 1 <= user_choice <= 4:            
                user_choice = lawyers[user_choice-1]
                return (user_choice)
            else:
                print("Invalid choice. Please choose a number between 1 and 4.")
        else:
            print("Invalid input. Please enter a number.")

def speak_narrator(filename):
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    wait_for_enter()

def speak_dramatically(text, gender):    
    if gender == 0:
        gender = "onyx"
    elif gender == 1:
        gender = "shimmer"
    else:
        gender = "echo"
    client = OpenAI()
    
    response = client.audio.speech.create(
        model="tts-1",
        voice=gender,
        input=text,
    )
    rmp3 = random.randint(0,999999999)
    filename = "audio/output" + str(rmp3) + ".mp3"
    response.stream_to_file(filename)
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    wait_for_enter()
    
def check_profanity(keyword):
    while True:
        profanity = predict([keyword])
        if profanity>0:
            keyword = input("Please avoid inappropriate language, enter a different keyword: ")
        else:
            return keyword
   
def text_generation(player, case, keyword1, keyword2, keyword3, keyword4):
    request = "Generate a persuasive closing argument in 3 sentences or less which highlights the following keywords in a natural way: " + keyword1 + keyword2 + keyword3 + keyword4
    client = OpenAI()

    completion = client.chat.completions.create(
      model="gpt-4",
      messages=[
        {"role": "system", "content": "You are a " + player + " lawyer attempting to give a persuasive closing argument for a " + case + "trial in 3 sentences or less."},
        {"role": "user", "content": request}
      ]
    )
    return (completion.choices[0].message.content)

def judgement(preference, p1arguments, p2arguments):
    request = "The prosecution's closing arguments are: " + p1arguments + "The desense's closing arguments are: " + p2arguments + "Provide a guilty or not guilt verdict and 1 sentence about why you made your decision."
    client = OpenAI()

    completion = client.chat.completions.create(
      model="gpt-4",
      messages=[
        {"role": "system", "content": "You are a judge and " + preference + ". You need to decide the case according to your personal opinion regarding the prosecution and defense attorney's closing arguments and not based on the law."},
        {"role": "user", "content": request}
      ]
    )
    return (completion.choices[0].message.content)

def is_valid_email(email):
    #Simple regex to check if an email address has a valid format.
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def get_email_addresses():
    #Prompts the user for email addresses, allows multiple entries separated by commas.
    emails = input("Enter the email addresses separated by a comma: ")
    email_list = [email.strip() for email in emails.split(',')]
    # Validate and collect valid email addresses
    valid_emails = [email for email in email_list if is_valid_email(email)]
    if not valid_emails:
        print("No valid email addresses entered.")
    return valid_emails

def ask_player_for_email(text_body):
    #Asks the player if they want an email and collects the addresses if they do.
    choice = input("Do you want an email of the case? (yes/no): ").lower()
    if choice in ['yes', 'y']:
        while True:
            email_addresses = get_email_addresses()
            if email_addresses:
                print("Email will be sent to the following addresses:", email_addresses)
                send_email(email_addresses, text_body)
                break   
            else:
                print("Invalid email address. Please enter a valid email address.")
        else:
            print("Moving on without sending emails.")

def send_email(email_addresses, text_body):
    # Email information
    sender_email = "lawyerupcapstoneproject@gmail.com"
    password = "ryhccofrjaxtccng"
    for receiver in email_addresses:
        receiver_email = receiver

        # Email server and port information
        smtp_server = "smtp.gmail.com"
        port = 587

        # Create the email message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Lawyer Up Case Summary"
        message["From"] = sender_email
        message["To"] = receiver_email

        # Attach the plain text message to the MIMEMultipart object
        part1 = MIMEText(text_body, "plain")
        message.attach(part1)

        try:
            # Connect to the SMTP server and send the email
            server = smtplib.SMTP(smtp_server, port)
            server.starttls()  # Secure the connection
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        except Exception as e:
            # Print any error messages to stdout
            print(e)
        finally:
            server.quit()

# Main function to simulate a game round
def simulate_round():
    #Clear the screen
    os.system('cls')
    
    #set the voice for narrator
    narrator_gender = 2
    
    #Display and announce the introduction
    print(intro)
    speak_narrator("audio/narrator1.mp3")
    
    #Generate Player's Lawyer choices
    print("Player 1, you are representing the prosecution.")
    lawyer1 = choose_lawyer()
    print("Player 2, you are the representing the defense.")
    lawyer2 = choose_lawyer()
    p1keyword1 = assign_avatar_and_keyword(lawyer1)
    p2keyword1 = assign_avatar_and_keyword(lawyer2)
    
    #Generate judge and case
    judge, preference = characterize_judge()
    case = generate_random_case()
    print("The defendant is being tried for " + case + ".")
    case_overview = "This case is presided over by the honorable " + judge + preference + ". The defendant is being tried for " + case + "."
    speak_dramatically(case_overview, narrator_gender)
    
    #Player1 inputs their keywords and crafts their closing argument
    speak_narrator("audio/narrator2.mp3")
    p1keyword2 = input("Player 1, enter your first keyword: ")
    p1keyword2 = check_profanity(p1keyword2)
    p1keyword3 = input("Player 1, enter your second keyword: ")
    p1keyword3 = check_profanity(p1keyword3)
    p1keyword4 = input("Player 1, enter your third keyword: ")
    p1keyword4 = check_profanity(p1keyword4)
    p1arguments = text_generation("prosecution", case, p1keyword1, p1keyword2, p1keyword3, p1keyword4)
    speak_narrator("audio/narrator3.mp3")
    print(p1arguments)
    if lawyer1 == "Eloquent Emma":
        gender = 1
    else:
        gender = 0
    speak_dramatically(p1arguments, gender)

    #Player2 inputs their keywords and crafts their rebuttle
    speak_narrator("audio/narrator4.mp3")
    p2keyword2 = input("Player 2, enter your first keyword: ")
    p2keyword2 = check_profanity(p2keyword2)
    p2keyword3 = input("Player 2, enter your second keyword: ")
    p2keyword3 = check_profanity(p2keyword3)
    p2keyword4 = input("Player 2, enter your third keyword: ")
    p2keyword4 = check_profanity(p2keyword4)
    p2arguments = text_generation("defense", case, p2keyword1, p2keyword2, p2keyword3, p2keyword4)
    speak_narrator("audio/narrator5.mp3")
    if lawyer2 == "Eloquent Emma":
        gender = 1
    else:
        gender = 0
    print(p2arguments)
    speak_dramatically(p2arguments, gender)
    
    #Generate and reveal a verdict from the judge
    speak_dramatically("All rise while " + judge + "reveals their verdict", narrator_gender)
    verdict = judgement(preference, p1arguments, p2arguments)
    print(verdict)
    if judge == "Judge Judy" or "Judge Jane":
        gender = 1
    else:
        gender = 0
    speak_dramatically(verdict, gender)
    
    #Clear screen and summarize case
    os.system('cls')
    month_year = now.strftime("%B, %Y")
    summary = "Here is a summary of your case.\n\n" + case_overview +  "\n\nProsecution closing arguments: " + p1arguments + "\n\nDefense closing arguments: " + p2arguments + "\n\n" + verdict + "\n\nThank you for playing!\nJason Jameson\n" + month_year
    print(summary)
    
    #Check if the players want the summary emailed to them
    ask_player_for_email(summary)

# Gameplay loop
while True:
    simulate_round()
    
    # Ask the user to press any key (Enter) to run again or a specific key to exit
    user_input = input("Press Enter to run again or type 'exit' and press Enter to stop: ")
    if user_input.lower() == 'exit':
        break