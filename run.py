import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from colorama import init, Fore
from datetime import datetime, timedelta

# Initialize colorama
init(autoreset=True)

# Path to your service account key file
# Load environment variables
SERVICE_ACCOUNT_FILE = os.environ.get('SERVICE_ACCOUNT_FILE', 'config/credentials.json')
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '14bxVzUbi3eNwJGfBIVK0wI4fzvu0Ork1lEA-wjoSjYk')  # Replace 'your-default-spreadsheet-id' with a default value or leave as an empty string

# Define the required scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Load credentials and create a service
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

# Spreadsheet range name (sheet name)
SHEET_NAME = os.environ.get('SHEET_NAME', 'testing')  # Replace 'testing' with your default sheet name or leave it as is

def load_worksheet():
    range_name = f'{SHEET_NAME}!A:E'  # Adjust the range as needed
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    return result.get('values', [])

def display_inventory():
    rows = load_worksheet()
    for row in rows:
        print(Fore.GREEN + f"Item: {row[0]}, Category: {row[1]}, Price: {row[2]}, Expiration Date: {row[3]}, Quantity: {row[4]}")

# Function to add a new item to the inventory
def add_item():
    # Taking inputs from the user, with the option to cancel the operation
    name = input(Fore.WHITE + "Enter item name (or type 'cancel' to exit): ")
    if name.lower() == 'cancel':
        return

    category = input(Fore.WHITE + "Enter item category (or type 'cancel' to exit): ")
    if category.lower() == 'cancel':
        return

    price = input(Fore.WHITE + "Enter item price (or type 'cancel' to exit): ")
    if price.lower() == 'cancel':
        return
    price = float(price)

    expiration_date = input(Fore.WHITE + "Enter expiration date (YYYY-MM-DD) (or type 'cancel' to exit): ")
    if expiration_date.lower() == 'cancel':
        return
    expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d')

    quantity = input(Fore.WHITE + "Enter item quantity (or type 'cancel' to exit): ")
    if quantity.lower() == 'cancel':
        return
    quantity = int(quantity)

    # Prepare the data to be appended
    values = [[name, category, price, expiration_date.strftime('%Y-%m-%d'), quantity]]
    body = {'values': values}

    # Append new item to the Google Sheet
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range=f'{SHEET_NAME}!A:E',
        valueInputOption='USER_ENTERED', body=body).execute()

    print(Fore.YELLOW + f"Item '{name}' added with details.")


def update_item():
    # Fetch current data
    rows = load_worksheet()

    # Taking inputs from the user
    name = input(Fore.WHITE + "Enter the name of the item to update (or type 'cancel' to exit): ")
    if name.lower() == 'cancel':
        return

    new_name = input(Fore.WHITE + "Enter new name (or press Enter to keep it the same, type 'cancel' to exit): ")
    if new_name.lower() == 'cancel':
        return

    new_category = input(Fore.WHITE + "Enter new category (or press Enter to keep it the same, type 'cancel' to exit): ")
    if new_category.lower() == 'cancel':
        return

    new_price = input(Fore.WHITE + "Enter new price (or press Enter to keep it the same, type 'cancel' to exit): ")
    if new_price.lower() == 'cancel':
        return
    new_price = float(new_price) if new_price else None

    new_expiration_date = input(Fore.WHITE + "Enter new expiration date (YYYY-MM-DD) (or press Enter to keep it the same, type 'cancel' to exit): ")
    if new_expiration_date.lower() == 'cancel':
        return
    new_expiration_date = datetime.strptime(new_expiration_date, '%Y-%m-%d') if new_expiration_date else None

    new_quantity = input(Fore.WHITE + "Enter new quantity (or press Enter to keep it the same, type 'cancel' to exit): ")
    if new_quantity.lower() == 'cancel':
        return
    new_quantity = int(new_quantity) if new_quantity else None

    # Searching for the item in the fetched data
    found = False
    for i, row in enumerate(rows):
        if row[0] == name:
            updates = [
                new_name or row[0],
                new_category or row[1],
                str(new_price if new_price is not None else row[2]),
                new_expiration_date.strftime('%Y-%m-%d') if new_expiration_date else row[3],
                str(new_quantity if new_quantity is not None else row[4])
            ]

            # API call to update the specific row
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f'{SHEET_NAME}!A{i+2}:E{i+2}',
                valueInputOption='USER_ENTERED',
                body={'values': [updates]}
            ).execute()

            found = True
            break

    # Notify user of update status
    if found:
        print(Fore.YELLOW + f"Details for '{name}' updated.")
    else:
        print(Fore.RED + f"Item '{name}' not found.")



def delete_item():
    # Fetch current data
    rows = load_worksheet()

    # Taking inputs from the user
    name = input(Fore.WHITE + "Enter the name of the item to delete (or type 'cancel' to exit): ")
    if name.lower() == 'cancel':
        return

    # Confirmation prompt
    confirm = input(Fore.YELLOW + f"Are you sure you want to delete '{name}'? Type YES to confirm or NO to cancel: ")
    if confirm.lower() != 'yes':
        print(Fore.GREEN + "Deletion cancelled.")
        return

    # Searching for the item in the fetched data
    found = False
    for i, row in enumerate(rows):
        if row[0] == name:
            # Preparing the request to delete the row
            requests = [{
                'deleteDimension': {
                    'range': {
                        'sheetId': 0,  # Assumes the sheet ID is 0, which is default for the first sheet
                        'dimension': 'ROWS',
                        'startIndex': i,  # Rows are zero-indexed in the API
                        'endIndex': i + 1
                    }
                }
            }]

            # API call to delete the row
            service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={'requests': requests}
            ).execute()

            found = True
            break

    # Notify user of update status
    if found:
        print(Fore.YELLOW + f"Item '{name}' deleted.")
    else:
        print(Fore.RED + f"Item '{name}' not found.")


def inventory_summary():
    rows = load_worksheet()
    # Skip the header row if your data includes headers
    rows = rows[1:] if rows and len(rows[0]) == 5 else rows

    total_items = 0
    category_count = {}
    total_quantity = 0

    for row in rows:
        # Ensure the row has the expected number of elements
        if len(row) >= 5:
            total_items += 1
            total_quantity += int(row[4])
            category = row[1]
            category_count[category] = category_count.get(category, 0) + 1

    print(Fore.MAGENTA + f"Total Items: {total_items}, Total Quantity: {total_quantity}")
    print(Fore.MAGENTA + "Category Summary:")
    for category, count in category_count.items():
        print(Fore.MAGENTA + f"  {category}: {count}")


def low_stock_alert(threshold=10):
    rows = load_worksheet()
    # Skip the header row if your data includes headers
    rows = rows[1:] if rows and len(rows[0]) == 5 else rows

    print(Fore.RED + "Low Stock Items:")
    for row in rows:
        # Ensure the row has enough elements and the quantity column is an integer
        if len(row) >= 5 and row[4].isdigit() and int(row[4]) < threshold:
            print(Fore.RED + f"  {row[0]} (Quantity: {row[4]})")


from datetime import datetime, timedelta

def expiration_warning(days=7):
    rows = load_worksheet()
    # Skip the header row if your data includes headers
    rows = rows[1:] if rows and len(rows[0]) == 5 else rows

    today = datetime.now()
    warning_date = today + timedelta(days=days)

    print(Fore.YELLOW + "Items Nearing Expiration Date:")
    for row in rows:
        # Ensure the row has enough elements and the expiration date column is a proper date string
        if len(row) >= 4 and isinstance(row[3], str):
            try:
                expiration_date = datetime.strptime(row[3], '%Y-%m-%d')
                if today <= expiration_date <= warning_date:
                    print(Fore.YELLOW + f"  {row[0]} (Expires on: {row[3]})")
            except ValueError:
                # Handle cases where the date format is incorrect
                pass


def search_by_category():
    rows = load_worksheet()
    # Skip the header row if your data includes headers
    rows = rows[1:] if rows and len(rows[0]) == 5 else rows

    category = input(Fore.WHITE + "Enter category to search (or type 'cancel' to exit): ")
    if category.lower() == 'cancel':
        return

    found = False
    for row in rows:
        # Ensure the row has enough elements
        if len(row) >= 5 and row[1] == category:
            expiration_date_str = row[3] if isinstance(row[3], str) else 'N/A'
            print(Fore.GREEN + f"Item: {row[0]}, Category: {row[1]}, Price: {row[2]}, Expiration Date: {expiration_date_str}, Quantity: {row[4]}")
            found = True

    if not found:
        print(Fore.RED + f"No items found in category '{category}'.")


def search_item():
    rows = load_worksheet()
    # Skip the header row if your data includes headers
    rows = rows[1:] if rows and len(rows[0]) == 5 else rows

    name = input(Fore.WHITE + "Enter item name to search (or type 'cancel' to exit): ")
    if name.lower() == 'cancel':
        return

    found = False
    for row in rows:
        # Ensure the row has enough elements
        if len(row) >= 5 and row[0] == name:
            expiration_date_str = row[3] if isinstance(row[3], str) else 'N/A'
            print(Fore.GREEN + f"Item: {row[0]}, Category: {row[1]}, Price: {row[2]}, Expiration Date: {expiration_date_str}, Quantity: {row[4]}")
            found = True
            break

    if not found:
        print(Fore.RED + f"Item '{name}' not found.")



    
# Main function to run the inventory management system
def main():
    print(Fore.CYAN + "\nWelcome to Supermarket Inventory Management System")

    while True:
        print(Fore.BLUE + "1. Display Inventory")
        print(Fore.BLUE + "2. Add Item")
        print(Fore.BLUE + "3. Update Item Details")
        print(Fore.BLUE + "4. Delete Item")
        print(Fore.BLUE + "5. Search for an Item")
        print(Fore.BLUE + "6. Search by Category")
        print(Fore.BLUE + "7. Inventory Summary")
        print(Fore.BLUE + "8. Low Stock Alert")
        print(Fore.BLUE + "9. Expiration Date Warning")
        print(Fore.BLUE + "10. Exit")
        choice = input(Fore.WHITE + "Enter your choice: ")

        if choice == '1':
            display_inventory()
        elif choice == '2':
            add_item()
        elif choice == '3':
            update_item()
        elif choice == '4':
            delete_item()
        elif choice == '5':
            search_item()
        elif choice == '6':
            search_by_category()
        elif choice == '7':
            inventory_summary()
        elif choice == '8':
            low_stock_alert()
        elif choice == '9':
            expiration_warning()
        elif choice == '10':
            print(Fore.RED + "Exiting the program. Goodbye!")
            break
        else:
            print(Fore.RED + "Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
