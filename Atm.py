import datetime
import os
import time
import sys
import random
import string

# Global variables
accounts = {}
current_account = None
running = True
ADMIN_PIN = "1234"
atm_cash = 5000.0  # ATM starts with $5000 cash
DAILY_LIMIT = 1000.0  # Default daily withdrawal limit

def generate_account_number():
    while True:
        acc_num = str(random.randint(1000, 9999))
        if acc_num not in accounts:
            return acc_num

def generate_card_number():
    existing_cards = {acc['card_number'] for acc in accounts.values()}
    while True:
        card_num = ''.join(random.choices(string.digits, k=16))
        if card_num not in existing_cards:
            return card_num

# Create a new account
def create_account(name, pin, initial_balance=0):
    account_number = generate_account_number()
    card_number = generate_card_number()

    accounts[account_number] = {
        'name': name,
        'pin': pin,
        'balance': initial_balance,
        'card_number': card_number,
        'transactions': [],
        'daily_withdrawals': 0.0,
        'last_withdraw_date': "",
        'daily_limit': DAILY_LIMIT
    }

    if initial_balance > 0:
        add_transaction(account_number, "Deposit", initial_balance, initial_balance)

    return account_number, card_number

# Add a transaction
def add_transaction(account_number, transaction_type, amount, balance_after):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    accounts[account_number]['transactions'].append({
        'type': transaction_type,
        'amount': amount,
        'timestamp': timestamp,
        'balance_after': balance_after
    })

# Verify PIN
def verify_pin(account_number, pin):
    return accounts.get(account_number, {}).get('pin') == pin

# Get account by card number
def get_account_by_card(card_number):
    for acc_num, acc_data in accounts.items():
        if acc_data['card_number'] == card_number:
            return acc_num
    return None

# Deposit
def deposit(account_number, amount):
    if amount <= 0:
        return False, "Deposit amount must be positive"
    accounts[account_number]['balance'] += amount
    add_transaction(account_number, "Deposit", amount, accounts[account_number]['balance'])
    return True, f"Deposited ${amount:.2f}. New balance: ${accounts[account_number]['balance']:.2f}"

# Withdraw
def withdraw(account_number, amount):
    global atm_cash
    today_str = datetime.date.today().isoformat()
    if accounts[account_number]['last_withdraw_date'] != today_str:
        accounts[account_number]['daily_withdrawals'] = 0.0
        accounts[account_number]['last_withdraw_date'] = today_str
    if amount <= 0:
        return False, "Withdrawal amount must be positive"
    if amount > accounts[account_number]['balance']:
        return False, "Insufficient funds"
    if accounts[account_number]['daily_withdrawals'] + amount > accounts[account_number]['daily_limit']:
        return False, f"Daily withdrawal limit of ${accounts[account_number]['daily_limit']:.2f} exceeded"
    if amount > atm_cash:
        return False, "ATM does not have enough cash"
    accounts[account_number]['balance'] -= amount
    accounts[account_number]['daily_withdrawals'] += amount
    atm_cash -= amount
    add_transaction(account_number, "Withdrawal", amount, accounts[account_number]['balance'])
    return True, f"Withdrew ${amount:.2f}. New balance: ${accounts[account_number]['balance']:.2f}"

# Transfer
def transfer(from_account, to_account, amount, pin):
    if from_account == to_account:
        return False, "Cannot transfer to the same account"
    if not verify_pin(from_account, pin):
        return False, "Invalid PIN"
    if amount <= 0:
        return False, "Transfer amount must be positive"
    if amount > accounts[from_account]['balance']:
        return False, "Insufficient funds"
    accounts[from_account]['balance'] -= amount
    add_transaction(from_account, "Transfer Out", amount, accounts[from_account]['balance'])
    accounts[to_account]['balance'] += amount
    add_transaction(to_account, "Transfer In", amount, accounts[to_account]['balance'])
    return True, f"Transferred ${amount:.2f} from {from_account} to {to_account}"

# Change PIN
def change_pin(account_number, old_pin, new_pin):
    if not verify_pin(account_number, old_pin):
        return False, "Incorrect PIN"
    if len(new_pin) != 4 or not new_pin.isdigit():
        return False, "PIN must be 4 digits"
    accounts[account_number]['pin'] = new_pin
    return True, "PIN changed successfully"

# Clear screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Show message
def show_message(message, error=False):
    clear_screen()
    print("=" * 60)
    print(" " * 20 + ("ERROR" if error else "MESSAGE") + " " * 20)
    print("=" * 60)
    print(f"\n{message}")

def display_welcome_screen():
    clear_screen()
    print("=" * 60)
    print(" " * 20 + "ATM SIMULATOR" + " " * 20)
    print("=" * 60)
    print("\nPlease insert your card (Enter card number):")
    print("(Type 'admin' to access admin panel or 'exit' to quit)")

# PIN verification
def pin_verification(account_number):
    attempts = 3
    while attempts > 0:
        clear_screen()
        print("=" * 60)
        print(" " * 20 + "PIN VERIFICATION" + " " * 20)
        print("=" * 60)
        print(f"\nCard: **** **** **** {accounts[account_number]['card_number'][-4:]}")
        print("\nPlease enter your PIN:")
        print(f"Attempts remaining: {attempts}")
        pin = input("\n> ").strip()
        if verify_pin(account_number, pin):
            return True
        else:
            attempts -= 1
            if attempts > 0:
                show_message("Incorrect PIN. Please try again.", error=True)
                time.sleep(2)
    show_message("Too many incorrect attempts. Card retained for security.", error=True)
    time.sleep(3)
    return False

# Main menu
def main_menu():
    global current_account
    while current_account:
        clear_screen()
        print("=" * 60)
        print(" " * 20 + "MAIN MENU" + " " * 20)
        print("=" * 60)
        print(f"\nWelcome, {accounts[current_account]['name']}")
        print(f"Account: {current_account}")
        print("\nPlease select an option:")
        print("1. Check Balance")
        print("2. Withdraw Cash")
        print("3. Deposit Cash")
        print("4. Transfer Funds")
        print("5. View Transaction History")
        print("6. Change PIN")
        print("7. Exit")
        choice = input("\n> ").strip()
        if choice == "1":
            check_balance()
        elif choice == "2":
            withdraw_cash()
        elif choice == "3":
            deposit_cash()
        elif choice == "4":
            transfer_funds()
        elif choice == "5":
            view_transaction_history()
        elif choice == "6":
            change_pin_menu()
        elif choice == "7":
            exit_session()
        else:
            show_message("Invalid option. Please try again.", error=True)
            time.sleep(2)

# Check balance
def check_balance():
    clear_screen()
    print("=" * 60)
    print(" " * 20 + "ACCOUNT BALANCE" + " " * 20)
    print("=" * 60)
    print(f"\nAccount: {current_account}")
    print(f"Available Balance: ${accounts[current_account]['balance']:.2f}")
    input("\nPress Enter to continue...")

# Withdraw cash (re-prompt)
def withdraw_cash():
    while True:
        clear_screen()
        print("=" * 60)
        print(" " * 20 + "WITHDRAW CASH" + " " * 20)
        print("=" * 60)
        print(f"\nAccount: {current_account}")
        print(f"Available Balance: ${accounts[current_account]['balance']:.2f}")
        print(f"ATM Cash Available: ${atm_cash:.2f}")
        print("\nSelect amount:")
        print("1. $20")
        print("2. $50")
        print("3. $100")
        print("4. $200")
        print("5. Other Amount")
        print("6. Cancel")
        choice = input("\n> ").strip()
        amount = 0
        if choice == "1": amount = 20
        elif choice == "2": amount = 50
        elif choice == "3": amount = 100
        elif choice == "4": amount = 200
        elif choice == "5":
            try:
                amount = float(input("\nEnter amount: $"))
                if amount <= 0:
                    show_message("Amount must be positive.", error=True)
                    time.sleep(2)
                    continue
            except ValueError:
                show_message("Invalid amount.", error=True)
                time.sleep(2)
                continue
        elif choice == "6":
            return
        else:
            show_message("Invalid option.", error=True)
            time.sleep(2)
            continue
        pin = input("\nEnter PIN for verification: ")
        if not verify_pin(current_account, pin):
            show_message("Incorrect PIN.", error=True)
            time.sleep(2)
            continue
        success, message = withdraw(current_account, amount)
        if success:
            show_message(message)
            process_withdrawal(amount)
        else:
            show_message(message, error=True)
            time.sleep(2)
            continue
        break

# Deposit cash (re-prompt)
def deposit_cash():
    while True:
        clear_screen()
        print("=" * 60)
        print(" " * 20 + "DEPOSIT CASH" + " " * 20)
        print("=" * 60)
        print(f"\nAccount: {current_account}")
        print(f"Current Balance: ${accounts[current_account]['balance']:.2f}")
        try:
            amount = float(input("\nEnter amount to deposit: $"))
            if amount <= 0:
                show_message("Amount must be positive.", error=True)
                time.sleep(2)
                continue
        except ValueError:
            show_message("Invalid amount.", error=True)
            time.sleep(2)
            continue
        pin = input("\nEnter PIN for verification: ")
        if not verify_pin(current_account, pin):
            show_message("Incorrect PIN.", error=True)
            time.sleep(2)
            continue
        success, message = deposit(current_account, amount)
        if success:
            show_message(message)
            receipt = input("\nWould you like a receipt? (y/n): ").lower()
            if receipt == 'y':
                print_receipt("Deposit", amount)
        else:
            show_message(message, error=True)
            time.sleep(2)
            continue
        break

# Transfer funds (re-prompt)
def transfer_funds():
    while True:
        clear_screen()
        print("=" * 60)
        print(" " * 20 + "TRANSFER FUNDS" + " " * 20)
        print("=" * 60)
        print(f"\nFrom Account: {current_account}")
        print(f"Available Balance: ${accounts[current_account]['balance']:.2f}")
        to_account = input("\nEnter recipient account number: ").strip()
        if to_account not in accounts:
            show_message("Account not found.", error=True)
            time.sleep(2)
            continue
        try:
            amount = float(input("\nEnter amount to transfer: $"))
            if amount <= 0:
                show_message("Amount must be positive.", error=True)
                time.sleep(2)
                continue
        except ValueError:
            show_message("Invalid amount.", error=True)
            time.sleep(2)
            continue
        pin = input("\nEnter PIN for verification: ")
        if not verify_pin(current_account, pin):
            show_message("Incorrect PIN.", error=True)
            time.sleep(2)
            continue
        success, message = transfer(current_account, to_account, amount, pin)
        if success:
            show_message(message)
            receipt = input("\nWould you like a receipt? (y/n): ").lower()
            if receipt == 'y':
                print_receipt("Transfer", amount, f"To: {to_account}")
        else:
            show_message(message, error=True)
            time.sleep(2)
            continue
        break

# Process withdrawal
def process_withdrawal(amount):
    clear_screen()
    print("=" * 60)
    print(" " * 20 + "PROCESSING WITHDRAWAL" + " " * 20)
    print("=" * 60)

    # Simulate cash dispensing
    print("\nPlease wait while your cash is being dispensed...")
    time.sleep(1)
    print("\nDispensing cash...")

    # Simulate counting and dispensing
    for i in range(3):
        print(".", end="")
        time.sleep(0.5)

    print(f"\n\n${amount:.2f} has been dispensed.")
    print("\nPlease take your cash.")
    print("\nReceipt will be printed.")

    # Print receipt
    receipt = input("\nWould you like a receipt? (y/n): ").lower()
    if receipt == 'y':
        print_receipt("Withdrawal", amount)

    input("\nPress Enter to continue...")

# View transaction history
def view_transaction_history():
    clear_screen()
    print("=" * 60)
    print(" " * 20 + "TRANSACTION HISTORY" + " " * 20)
    print("=" * 60)
    print(f"\nAccount: {current_account}")

    transactions = accounts[current_account]['transactions']

    if not transactions:
        print("\nNo transactions found.")
    else:
        print("\nRecent Transactions:")
        print("-" * 60)
        print(f"{'Type':<12} {'Amount':<10} {'Balance':<15} {'Date & Time'}")
        print("-" * 60)

        # Show last 10 transactions
        for transaction in transactions[-10:]:
            print(f"{transaction['type']:<12} ${transaction['amount']:<9.2f} ${transaction['balance_after']:<14.2f} {transaction['timestamp']}")

    input("\nPress Enter to continue...")

# Change PIN menu
def change_pin_menu():
    clear_screen()
    print("=" * 60)
    print(" " * 20 + "CHANGE PIN" + " " * 20)
    print("=" * 60)
    print(f"\nAccount: {current_account}")

    # Verify current PIN
    current_pin = input("\nEnter current PIN: ")
    if not verify_pin(current_account, current_pin):
        show_message("Incorrect PIN.", error=True)
        time.sleep(2)
        return

    # Enter new PIN
    new_pin = input("\nEnter new PIN (4 digits): ")
    if len(new_pin) != 4 or not new_pin.isdigit():
        show_message("PIN must be 4 digits.", error=True)
        time.sleep(2)
        return

    # Confirm new PIN
    confirm_pin = input("\nConfirm new PIN: ")
    if new_pin != confirm_pin:
        show_message("PINs do not match.", error=True)
        time.sleep(2)
        return

    # Update PIN
    success, message = change_pin(current_account, current_pin, new_pin)
    if success:
        show_message(message)
    else:
        show_message(message, error=True)

    time.sleep(2)

def exit_session():
    global current_account

    clear_screen()
    print("=" * 60)
    print(" " * 20 + "SESSION ENDING" + " " * 20)
    print("=" * 60)
    print("\nThank you for using our ATM.")
    print("Please take your card.")

    # Simulate card return
    time.sleep(2)
    print("\nYour card is being returned...")
    time.sleep(1)

    current_account = None
    time.sleep(1)

# Print receipt
def print_receipt(transaction_type, amount, additional_info=""):
    clear_screen()
    print("=" * 60)
    print(" " * 15 + "ATM TRANSACTION RECEIPT" + " " * 15)
    print("=" * 60)
    print(f"\nDate: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"ATM ID: ATM001")
    print(f"Card: **** **** **** {accounts[current_account]['card_number'][-4:]}")
    print(f"Account: {current_account}")
    print(f"\nTransaction: {transaction_type}")
    if additional_info:
        print(additional_info)
    print(f"Amount: ${amount:.2f}")
    print(f"Balance: ${accounts[current_account]['balance']:.2f}")
    print("\nThank you for using our ATM!")

    input("\nPress Enter to continue...")

# Admin panel
def admin_panel():
    attempts = 3

    while attempts > 0:
        clear_screen()
        print("=" * 60)
        print(" " * 20 + "ADMIN PANEL" + " " * 20)
        print("=" * 60)
        print(f"\nAttempts remaining: {attempts}")
        print("\nPlease enter admin PIN:")

        pin = input("\n> ").strip()

        if pin == ADMIN_PIN:
            admin_menu()
            return
        else:
            attempts -= 1
            if attempts > 0:
                show_message("Incorrect PIN. Please try again.", error=True)
                time.sleep(2)

    show_message("Too many incorrect attempts. Returning to welcome screen.", error=True)
    time.sleep(2)

# Admin menu
def admin_menu():
    while True:
        clear_screen()
        print("=" * 60)
        print(" " * 20 + "ADMIN MENU" + " " * 20)
        print("=" * 60)
        print("\nPlease select an option:")
        print("1. Create New Account")
        print("2. View All Accounts")
        print("3. Exit Admin Panel")

        choice = input("\n> ").strip()

        if choice == "1":
            create_account_menu()
        elif choice == "2":
            view_all_accounts()
        elif choice == "3":
            return
        else:
            show_message("Invalid option. Please try again.", error=True)
            time.sleep(2)

# Create account menu
def create_account_menu():
    clear_screen()
    print("=" * 60)
    print(" " * 20 + "CREATE ACCOUNT" + " " * 20)
    print("=" * 60)

    name = input("\nEnter full name: ").strip()
    if not name:
        show_message("Name cannot be empty.", error=True)
        time.sleep(2)
        return

    pin = input("\nCreate a 4-digit PIN: ").strip()
    if len(pin) != 4 or not pin.isdigit():
        show_message("PIN must be 4 digits.", error=True)
        time.sleep(2)
        return

    confirm_pin = input("\nConfirm PIN: ").strip()
    if pin != confirm_pin:
        show_message("PINs do not match.", error=True)
        time.sleep(2)
        return

    try:
        initial_deposit = float(input("\nEnter initial deposit (optional, press Enter to skip): ") or "0")
        if initial_deposit < 0:
            show_message("Initial deposit cannot be negative.", error=True)
            time.sleep(2)
            return
    except ValueError:
        show_message("Invalid amount. Setting initial deposit to $0.", error=True)
        initial_deposit = 0

    account_number, card_number = create_account(name, pin, initial_deposit)

    show_message(f"Account created successfully!")
    print(f"\nAccount Number: {account_number}")
    print(f"Card Number: {card_number}")
    print(f"Initial Balance: ${initial_deposit:.2f}")

    input("\nPress Enter to continue...")

# View all accounts
def view_all_accounts():
    clear_screen()
    print("=" * 60)
    print(" " * 20 + "ALL ACCOUNTS" + " " * 20)
    print("=" * 60)

    if not accounts:
        print("\nNo accounts found.")
    else:
        print("\nAccount Details:")
        print("-" * 80)
        print(f"{'Account #':<12} {'Name':<20} {'Card #':<20} {'Balance':<15}")
        print("-" * 80)

        for acc_num, acc_data in accounts.items():
            print(f"{acc_num:<12} {acc_data['name']:<20} {acc_data['card_number'][-4:]:<20} ${acc_data['balance']:<14.2f}")

    input("\nPress Enter to continue...")

def shutdown():
    clear_screen()
    print("=" * 60)
    print(" " * 20 + "SHUTTING DOWN" + " " * 20)
    print("=" * 60)
    print("\nATM is shutting down...")
    time.sleep(2)
    global running
    running = False
    clear_screen()

def main():
    global current_account
    while running:
        display_welcome_screen()
        card_input = input("\n> ").strip()

        if card_input.lower() == 'exit':
            shutdown()
            continue
        if card_input.lower() == 'admin':
            admin_panel()
            continue
        if len(card_input) != 16 or not card_input.isdigit():
            show_message("Invalid card number. Please try again.", error=True)
            time.sleep(2)
            continue
        account_number = get_account_by_card(card_input)
        if not account_number:
            show_message("Card not recognized. Please try again.", error=True)
            time.sleep(2)
            continue
        current_account = account_number
        if pin_verification(current_account):
            main_menu()

if __name__ == "__main__":
    main()    