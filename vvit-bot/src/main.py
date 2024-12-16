import flet as ft
import time, os
import requests
from dotenv import load_dotenv
import model

load_dotenv()

# Firebase Authentication URLs
firebase_auth_url = os.getenv("FIRE_LOGIN")
firebase_signup_url = os.getenv("FIRE_SIGN_UP")

def main_style():
    return {
        "width": 420,
        "height": 500,
        "bgcolor": "#141518",
        "border_radius": 15,
        "padding": 15
    }

def prompt_style():
    return {
        "width": 420,
        "height": 45,
        "border_radius": 15,
        "border_color": "white",
        "content_padding": 15,
        "cursor_color": "white",
    }

class CreateMessage(ft.Column):
    def __init__(self, name, message, is_markdown=False):
        self.name = name
        self.is_markdown = is_markdown
        self.message = message
        self.text = ft.Text(self.message) if not is_markdown else ft.Markdown(self.message)
        super().__init__(spacing=4)
        self.controls = [
            ft.Text(self.name, opacity=0.6),
            self.text
        ]

class MainContentArea(ft.Container):
    def __init__(self):
        super().__init__(**main_style())
        self.chat = ft.ListView(
            expand=True,
            height=200,
            spacing=15,
            auto_scroll=True
        )
        self.content = self.chat

class Prompt(ft.TextField):
    def __init__(self, chat: ft.ListView, submit_action):
        super().__init__(**prompt_style(), on_submit=self.run_prompt)
        self.chat = chat
        self.submit_action = submit_action

    def animation(self, name, prompt, is_markdown=False):
        word_list = []
        message = CreateMessage(name, "", is_markdown)
        self.chat.controls.append(message)
        self.chat.update()  
        
        for word in list(prompt):
            word_list.append(word)
            message.text.value = "".join(word_list)  
            self.chat.update()  
            time.sleep(0.008)  

    def user_output(self, prompt):
        message = CreateMessage("You", prompt)
        self.chat.controls.append(message)
        self.chat.update()

    def model_output(self, prompt):
        response = model.response_with_memory(prompt) # Replace this with a model call if needed
        self.animation("Bot", response, is_markdown=True)

    def run_prompt(self, event):
        text = event.control.value
        self.user_output(text)  
        self.value = ""  
        self.update()
        self.model_output(text)  

    def submit_prompt(self, e):
        text = self.value
        self.user_output(text)
        self.value = ""  
        self.update()
        self.model_output(text)  

def logout(page: ft.Page, show_login_page):
    # Clear any session or authentication data if necessary
    page.clean()  # Clean the page and show the login page
    show_login_page(page, show_chat_interface)  # Redirect to the login page

def show_signup_page(page: ft.Page, show_login_page, show_chat_interface):
    page.clean()

    email_field = ft.TextField(label="Email", hint_text="Enter your email", width=300)
    password_field = ft.TextField(label="Password", hint_text="Enter your password", password=True, width=300)
    message_text = ft.Text("")

    def signup_clicked(e):
        email = email_field.value
        password = password_field.value

        if "@" not in email or "." not in email:
            message_text.value = "Invalid email format."
            page.update()
            return

        if len(password) < 6:
            message_text.value = "Password must be at least 6 characters long."
            page.update()
            return

        try:
            response = requests.post(firebase_signup_url, json={
                "email": email,
                "password": password,
                "returnSecureToken": True
            })

            data = response.json()
            if "error" in data:
                message_text.value = f"Error: {data['error']['message']}"
            else:
                message_text.value = "Account created successfully! Please log in."
                page.update()
                show_login_page(page, show_chat_interface)
        except Exception as e:
            message_text.value = f"Error: {str(e)}"
            page.update()

    signup_button = ft.ElevatedButton(text="Sign Up", on_click=signup_clicked)
    login_button = ft.TextButton(text="Already have an account? Log in", on_click=lambda e: show_login_page(page, show_chat_interface))

    page.add(
        ft.Column(
            [
                ft.Text("Signup Page", style="headlineMedium"),
                email_field,
                password_field,
                signup_button,
                login_button,
                message_text
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO
        )
    )
    page.update()

def show_login_page(page: ft.Page, show_chat_interface):
    page.clean()

    email_field = ft.TextField(label="Email", hint_text="Enter your email", width=300)
    password_field = ft.TextField(label="Password", hint_text="Enter your password", password=True, width=300)
    message_text = ft.Text("")

    def login_clicked(e):
        email = email_field.value
        password = password_field.value

        if "@" not in email or "." not in email:
            message_text.value = "Invalid email format."
            page.update()
            return

        try:
            response = requests.post(firebase_auth_url, json={
                "email": email,
                "password": password,
                "returnSecureToken": True
            })

            data = response.json()
            if "error" in data:
                message_text.value = f"Error: {data['error']['message']}"
            else:
                message_text.value = "Login successful!"
                page.update()
                show_chat_interface(page, email)  # After successful login, show the chatbot interface
        except Exception as e:
            message_text.value = f"Error: {str(e)}"
            page.update()

    login_button = ft.ElevatedButton(text="Log In", on_click=login_clicked)
    signup_button = ft.TextButton(text="Don't have an account? Sign up", on_click=lambda e: show_signup_page(page, show_login_page, show_chat_interface))

    page.add(
        ft.Column(
            [
                ft.Text("Login Page", style="headlineMedium"),
                email_field,
                password_field,
                login_button,
                signup_button,
                message_text
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO
        )
    )
    page.update()

def show_chat_interface(page: ft.Page, email):
    page.clean()

    main = MainContentArea()
    prompt = Prompt(chat=main.chat, submit_action=None)
    
    # Create submit and logout buttons next to each other
    submit_button = ft.ElevatedButton(text="Submit", on_click=prompt.submit_prompt)
    logout_button = ft.ElevatedButton(text="Logout", on_click=lambda e: logout(page, show_login_page))
    
    # Add the buttons in a row
    button_row = ft.Row([submit_button, logout_button], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

    page.add(
        ft.Text(f"Welcome {email}", text_align="center", size=24, weight="bold"),
        main,
        ft.Divider(height=6, color="transparent"),
        prompt,
        button_row  # Add the row with buttons
    )
    page.update()

def main(page: ft.Page):
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    page.theme_mode = "dark"

    show_login_page(page, show_chat_interface)  # Start with the login page

if __name__ == '__main__':
    ft.app(target=main)
