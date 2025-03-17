import pickle
from datetime import datetime, timedelta
from collections import UserDict
from typing import Callable
from functools import wraps
from random import choice
from colorama import Fore

class PhoneValidationError(Exception):
    pass

class MissingPhoneError(Exception):
    pass

class DateValidationError(Exception):
    pass

class Field:
    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Birthday(Field):
    def __init__(self, value: str):
        try:
            if datetime.strptime(value, "%d.%m.%Y"):
                super().__init__(value)
        except ValueError as exc:
            raise DateValidationError("Invalid date (try using DD.MM.YYYY format)") from exc
        
class Phone(Field):
    def __init__(self, value: str):
        if len(value) != 10:
            raise PhoneValidationError("Phone number must be 10 digits long")
        if not value.isdigit():
            raise PhoneValidationError("Phone number must contain digits only")
        super().__init__(value)

class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    # Method to find a phone number
    def find_phone(self, phone: str) -> Phone | None:
        for ph in self.phones:
            if phone == ph.value:
                return ph
        return None
    
    # Method to add a new phone number
    def add_phone(self, phone: str):
        phone = Phone(phone)
        if phone.value not in [ph.value for ph in self.phones]:
            self.phones.append(phone)
    
    # Method to remove a phone number
    def remove_phone(self, phone: str):
        self.phones = [ph for ph in self.phones if ph.value != phone]
    
    # Method to edit an existing phone number
    def edit_phone(self, old_phone: str, new_phone: str):
        if self.find_phone(old_phone):
            self.add_phone(new_phone)
            self.remove_phone(old_phone)
        else:
            raise MissingPhoneError("Phone number to be edited is missing from the list")
    
    # Method to add birthday
    def add_birthday(self, birthday: str):
        self.birthday = Birthday(birthday)
        
    def __str__(self):
        return f"Contact name: {self.name.value}; phone(s): {', '.join(p.value for p in self.phones)}{f"; birthday: {self.birthday}" if self.birthday else ""}"

class AddressBook(UserDict):

    # Method to add a record
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    # Method to find a record
    def find(self, name: str) -> Phone | None:
        if name in self.data:
            return self.data[name]
        return None
    
    # Method to delete an existing record
    def delete(self, name: str):
        if name in self.data:
            self.data.pop(name)

    @staticmethod
    def date_to_string(date: datetime) -> str:
        return date.strftime("%d.%m.%Y")

    @staticmethod
    def find_next_weekday(start_date: datetime, weekday: datetime) -> datetime:
        days_ahead = weekday - start_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return start_date + timedelta(days=days_ahead)

    @staticmethod
    def adjust_for_weekend(birthday: datetime) -> datetime:
        if birthday.weekday() >= 5:
            return AddressBook.find_next_weekday(birthday, 0)
        return birthday

    # Method to get upcoming birthdays
    def get_upcoming_birthdays(self):
        upcoming_birthdays = []
        today = datetime.today()
        for name in self.data:
            if self.data[name].birthday:
                birthday = datetime.strptime(self.data[name].birthday.value, "%d.%m.%Y")
                birthday_this_year = birthday.replace(year=today.year)
                if birthday_this_year.toordinal() < today.toordinal():
                    birthday_this_year = birthday.replace(year=today.year+1)
                if 0 <= (birthday_this_year.toordinal() - today.toordinal()) <= 7:
                    birthday_this_year = AddressBook.adjust_for_weekend(birthday_this_year)
                    congratulation_date_str = AddressBook.date_to_string(birthday_this_year)
                    upcoming_birthdays.append({"name": name, "congratulation_date": congratulation_date_str})
        return upcoming_birthdays

    def __str__(self):
        return "\n".join(record.__str__() for record in self.data.values())

# Decorator to handle input errors
def input_error(func: Callable):
    """
    Handles various types of input errors

    Parameters:
        func (callable): a function processing user input
    """
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return f"{Fore.RED}\nInvalid command format (name/phone missing)"
        except IndexError:
            return f"{Fore.RED}\nEnter argument for the command please"
        except (KeyError, AttributeError):
            return f"{Fore.RED}\nContact doesn't exist"
        except (PhoneValidationError, MissingPhoneError, DateValidationError) as e:
            return f"{Fore.RED}\n{e}"
    return inner

# Function to parse user's input
def parse_input(user_input: str) -> tuple[str, list[str]]:
    """
    Extracts data from user's input

    Parameters:
        user input (str): user's input as a single string
    
    Returns:
        tuple[str, list[str]]: a tuple with command as first element and list of arguments
            as second element
    """
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

# Function to add contact
@input_error
def add_contact(args: list[str], book: AddressBook) -> str:
    """
    Creates a new contact (or overwrites an existing one)

    Parameters:
        args (list[str]): new contact data (name, phone)
        book (AddressBook): existing contacts
    
    Returns:
        str: formatted string with notification
    """
    name, phone, *_ = args
    if book.find(name):
        book[name].add_phone(phone)
    else:
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)
    return f"{Fore.GREEN}\nContact/phone added: {name} {phone}"

# Function to change contact
@input_error
def change_contact(args: list[str], book: AddressBook) -> str:
    """
    Changes phone number of an existing contact

    Parameters:
        args (list[str]): new contact data (name, phone)
        book (AddressBook): existing contacts
    
    Returns:
        str: formatted string with notification
    """
    name, old_phone, new_phone, *_ = args
    book.find(name).edit_phone(old_phone, new_phone)
    return f"{Fore.GREEN}\n{name}: phone {old_phone} changed to {new_phone}"

# Function to show contact
@input_error
def show_phone(args: list[str], book: AddressBook) -> str:
    """
    Shows phone number of a contact

    Parameters:
        args (list[str]): contact data (name)
        book (AddressBook): existing contacts
    
    Returns:
        str: formatted string with notification
    """
    name = args[0]
    return f"{Fore.GREEN}\n{name}: {'; '.join(p.value for p in book[name].phones)}"

# Function to add birthday
@input_error
def add_birthday(args: list[str], book: AddressBook) -> str:
    """
    Adds birthday to contact

    Parameters:
        args (list[str]): contact data (name)
        book (AddressBook): existing contacts

    Returns:
        str: formatted string with notification
    """
    name, birthday, *_ = args
    book.data[name].add_birthday(birthday)
    return f"{Fore.GREEN}\nBirthday added: {name} {birthday}"

# Function to show birthday
@input_error
def show_birthday(args: list[str], book: AddressBook) -> str:
    """
    Shows contact's birthday

    Parameters:
        args (list[str]): contact data (name)
        book (AddressBook): existing contacts

    Returns:
        str: formatted string with notification
    """
    name = args[0]
    if book.find(name):
        if book[name].birthday:
            return f"{Fore.GREEN}\n{name}: {book[name].birthday}"
        return Fore.GREEN + f"\nThere is no birthday for {name} yet"
    return Fore.GREEN + f"\nContact \"{name}\" doesn't exist"

# Function to show congratulation dates
@input_error
def birthdays(book: AddressBook) -> str:
    """
    Shows congratulations date for the next 7 days

    Parameters:
        book (AddressBook): existing contacts

    Returns:
        str: formatted string with notification
    """
    if book.get_upcoming_birthdays():
        return f"{Fore.GREEN}\nDon't forget to congratulate:\n\n{"\n".join(f"{item["name"]} on {item["congratulation_date"]}" for item in book.get_upcoming_birthdays())}"
    return f"{Fore.GREEN}\nCongratulation list is empty"

# Function to show all contacts
def show_all_contacts(book: AddressBook) -> str:
    """
    Shows all contacts

    Parameters:
        book (AddressBook): existing contacts
    
    Returns:
        str: formatted string with information/notification
    """
    if len(book) == 0:
        return Fore.GREEN + "\nThere are no contacts yet"
    return f"\n{Fore.GREEN}{book}"

# Function to save contact book to a file
def save_data(book: AddressBook, filename="addressbook.pkl"):
    """
    Saves contacts to a pkl file

    Parameters:
        book (AddressBook): existing contacts
        filename (str): path to a pkl file with contacts
    
    Returns:
        None
    """
    with open(filename, "wb") as f:
        pickle.dump(book, f)

# Function to load contact book from a file
def load_data(filename="addressbook.pkl") -> AddressBook:
    """
    Loads contacts from a pkl file

    Parameters:
        filename (str): path to a pkl file with contacts
    
    Returns:
        book (AddressBook): existing contacts
    """
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

# Main function
def main():
    """
    Handles phone bot operations
    """
    colours = (Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE)
    bot_banner = f"""{choice(colours)}\
 ██▓███   ██░ ██  ▒█████   ███▄    █ ▓█████     ▄▄▄▄    ▒█████  ▄▄▄█████▓
▓██░  ██▒▓██░ ██▒▒██▒  ██▒ ██ ▀█   █ ▓█   ▀    ▓█████▄ ▒██▒  ██▒▓  ██▒ ▓▒
▓██░ ██▓▒▒██▀▀██░▒██░  ██▒▓██  ▀█ ██▒▒███      ▒██▒ ▄██▒██░  ██▒▒ ▓██░ ▒░
▒██▄█▓▒ ▒░▓█ ░██ ▒██   ██░▓██▒  ▐▌██▒▒▓█  ▄    ▒██░ █▀  ▒██   ██░░ ▓██▓ ░ 
▒██▒ ░  ░░▓█▒░██▓░ ████▓▒░▒██░   ▓██░░▒████▒   ░▓█  ▀█▓░ ████▓▒░  ▒██▒ ░ 
▒▓▒░ ░  ░ ▒ ░░▒░▒░ ▒░▒░▒░ ░ ▒░   ▒ ▒ ░░ ▒░ ░   ░▒▓███▀▒░ ▒░▒░▒░   ▒ ░░   
░▒ ░      ▒ ░▒░ ░  ░ ▒ ▒░ ░ ░░   ░ ▒░ ░ ░  ░   ▒░▒   ░   ░ ▒ ▒░     ░    
░░        ░  ░░ ░░ ░ ░ ▒     ░   ░ ░    ░       ░    ░ ░ ░ ░ ▒    ░      
          ░  ░  ░    ░ ░           ░    ░  ░    ░          ░ ░           
                                                     ░                   """
    print(bot_banner + "\n")
    print(Fore.GREEN + "Welcome to the assistant bot!".upper())
    command_list = f"""
    {Fore.BLUE + "List of available commands".upper()}:

    {Fore.WHITE}hello {Fore.BLUE}- say hello to the bot
    {Fore.WHITE}help {Fore.BLUE}- show list of commands
    {Fore.WHITE}add <username> <phone> {Fore.BLUE}- add a new contact with phone number
    {Fore.WHITE}change <username> <old phone> <new phone>{Fore.BLUE}- change phone number
    {Fore.WHITE}phone <username> {Fore.BLUE}- show phone number
    {Fore.WHITE}add-birthday <username> <birthday (dd.mm.YYYY)>{Fore.BLUE}- add/change birthday
    {Fore.WHITE}show-birthday <username> {Fore.BLUE}- show birthday
    {Fore.WHITE}birthdays {Fore.BLUE}- show all congratulation dates within the next 7 days
    {Fore.WHITE}all {Fore.BLUE}- show all contacts
    {Fore.WHITE}exit {Fore.BLUE}- exit the bot
    {Fore.WHITE}close {Fore.BLUE}- exit the bot
    """
    print(command_list, end="")
    book = load_data()
    while True:
        user_input = input(Fore.YELLOW + "\nEnter a command: " + Fore.WHITE)
        command, *args = parse_input(user_input)
        # 'Exit' or 'close' commands
        if command in ("exit", "close"):
            save_data(book)
            print(Fore.GREEN + "\nGoodbye!".upper())
            break
        # 'Hello' command
        if command == "hello":
            print(Fore.WHITE + "\nHow can I help you?")
        # 'Help' command
        elif command == "help":
            print(command_list, end="")
        # 'Add' command
        elif command == "add":
            print(add_contact(args, book))
        # 'Change' command
        elif command == "change":
            print(change_contact(args, book))
        # 'Phone' command
        elif command == "phone":
            print(show_phone(args, book))
        # 'add-birthday' command
        elif command == "add-birthday":
            print(add_birthday(args, book))
        # 'show-birthday' command
        elif command == "show-birthday":
            print(show_birthday(args, book))
        # 'birthdays' command
        elif command == "birthdays":
            print(birthdays(book))
        # 'All' command
        elif command == "all":
            print(show_all_contacts(book))
        # Command absent from command list
        else:
            print(Fore.RED + "\nInvalid command")
    print(Fore.RESET, end="")

if __name__ == "__main__":
    main()
