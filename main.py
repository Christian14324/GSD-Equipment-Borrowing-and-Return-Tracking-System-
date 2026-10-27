"""GSD Equipment Borrowing and Return Tracking System"""

from datetime import date


def get_next_id(data, record_type):
    """Return and reserve the next unique ID for the requested record type."""
    record_id = data["next_ids"][record_type]
    data["next_ids"][record_type] = record_id + 1
    return record_id


def find_by_id(records, record_id):
    """Find one dictionary in a list by its ID, or return None"""
    for record in records:
        if record["id"] == record_id:
            return record
    return None


def find_user(data, username, password):
    """Authenticate a staff member or registered student using their credentials."""
    for user in data["staff"]:
        if user["username"] == username and user["password"] == password:
            return user

    for user in data["students"]:
        if user["username"] == username and user["password"] == password:
            return user
    return None


def username_exists(data, username):
    """Check whether a username is already used by any account."""
    for user in data["staff"]:
        if user["username"] == username:
            return True

    for user in data["students"]:
        if user["username"] == username:
            return True
    return False

def full_name_exists(data, name):
    """Check whether a full name is already used by any account."""
    for user in data["staff"]:
        if user["name"] == name:
            return True

    for user in data["students"]:
        if user["name"] == name:
            return True
    return False

def school_id_exists(data, school_id):
    """Check whether a school ID is already used by any account."""
    for user in data["staff"]:
        if user["school_id"] == school_id:
            return True

    for user in data["students"]:
        if user["school_id"] == school_id:
            return True
    return False


def register_student(data, first_name, middle_name, last_name, school_id, username, password):
    """Validate registration details and add a new student account when valid."""
    # Check the text exactly as entered before normalization so punctuation,
    # numbers, tabs, and other pasted special characters cannot be removed
    # and accepted later.
    first_name = normalize_full_name(first_name)
    middle_name = normalize_full_name(middle_name)
    last_name = normalize_full_name(last_name)
    name = " ".join([first_name, middle_name, last_name])
    school_id = school_id.strip()
    username = username.strip()

    if (
        first_name == "" or middle_name == "" or last_name == "" or
        school_id == "" or username == "" or password == ""
    ):
        return False, "Please fill in all fields."
    if len(password) < 8:
        return False, "Password must contain at least 8 characters."
    if not is_school_id(school_id):
        return False, "School ID must contain 12 digits."
    if not is_username(username):
        return False, "Username must start with letters and may end with numbers only"
    if username_exists(data, username):
        return False, "This username is already used."
    if not is_full_name(first_name):
        return False, "First name must contain letters"
    if not is_full_name(middle_name):
        return False, "Middle name must contain letters"
    if not is_full_name(last_name):
        return False, "Last name must contain letters"
    if full_name_exists(data, name):
        return False, "This full name is already used."
    if school_id_exists(data, school_id):
        return False, "This school ID is already used."

    new_student = {
        "id": get_next_id(data, "student"),
        "role": "student",
        "name": name,
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "school_id": school_id,
        "username": username,
        "password": password,
    }
    data["students"].append(new_student)
    return True, "Student account created. You can now sign in."


def asset_number_exists(data, asset_number):
    """Check whether an equipment asset number is already registered."""
    for item in data["equipment"]:
        if item["asset_number"] == asset_number:
            return True
    return False


def add_equipment(data, name, asset_number, quantity):
    """Validate and store a new equipment item."""
    name = normalize_text(name)
    asset_number = asset_number.strip()
    quantity = quantity.strip()

    if name == "" or asset_number == "" or quantity == "":
        return False, "Please fill in all fields."
    if not quantity.isdigit() or int(quantity) < 1:
        return False, "Quantity must be a whole number greater than zero."
    if asset_number_exists(data, asset_number):
        return False, "This asset number already exists."

    new_item = {
        "id": get_next_id(data, "equipment"),
        "name": name,
        "category": "Electronics",
        "asset_number": asset_number,
        "quantity": int(quantity),
        "condition": "Good",
    }
    data["equipment"].append(new_item)
    return True, "Equipment added successfully."


def edit_equipment_condition(data, equipment_id, condition):
    """Change an item's physical condition."""
    item = find_by_id(data["equipment"], equipment_id)
    if item == None:
        return False, "Equipment ID was not found."

    if condition != "Good" and condition != "Damaged" and condition != "Needs Repair":
        return False, "Choose Good, Damaged, or Needs Repair."

    item["condition"] = condition
    return True, "Equipment condition updated."


def equipment_status(data, item):
    """Calculate availability from the item's condition and remaining stock."""
    if item["condition"] != "Good":
        return "Not Available"
    if item["quantity"] < 1:
        return "Not Available"
    return "Available"


def request_borrowing(data, student, equipment_id):
    """Create a pending borrowing request for available equipment."""
    item = find_by_id(data["equipment"], equipment_id)
    if item == None:
        return False, "Equipment ID was not found."
    if equipment_status(data, item) != "Available":
        return False, "This equipment is not available."

    # Start record numbering over only when no borrowing history exists.
    if data["borrowings"] == []:
        data["next_ids"]["borrowing"] = 1

    # Quantity represents the number of units still available.  Reserve one
    # unit as soon as the student sends a request, including while it is pending.
    item["quantity"] -= 1
    new_record = {
        "id": get_next_id(data, "borrowing"),
        "equipment_id": item["id"],
        "student_id": student["id"],
        "borrowed_date": "Not approved yet",
        "due_date": "Not set",
        "returned_date": "Not returned",
        "status": "Pending",
        "return_condition": "Not checked",
        "notes": "",
    }
    data["borrowings"].append(new_record)
    return True, "Borrowing request sent to staff."


def is_full_name(value):
    """Return True only for a non-empty name made from ASCII letters and spaces."""
    return value != "" and all(
        ("A" <= character <= "Z") or ("a" <= character <= "z") or character == " "
        for character in value
    )


def normalize_full_name(value):
    """Format one name field without changing letters the user capitalized."""
    return normalize_text(value)


def normalize_text(value):
    """Trim text and capitalize its first letter without lowercasing the rest."""
    text = " ".join(value.strip().split())
    if text == "":
        return ""
    return text[0].upper() + text[1:]


def is_username(value):
    """Return True for ASCII letters, optionally followed by digits, with no spaces."""
    if value == "" or not ("A" <= value[0] <= "Z" or "a" <= value[0] <= "z"):
        return False

    has_number = False
    for character in value:
        is_letter = "A" <= character <= "Z" or "a" <= character <= "z"
        if is_letter and not has_number:
            continue
        if "0" <= character <= "9":
            has_number = True
            continue
        return False

    return True


def is_school_id(value):
    """Return True for exactly 12 digits, with optional hyphens."""
    digits = 0
    for character in value:
        if "0" <= character <= "9":
            digits += 1
        elif character != "-":
            return False
    return digits == 12


def parse_date(date_text):
    """Parse a valid date written in YYYY-MM-DD format."""
    if len(date_text) != 10 or date_text[4] != "-" or date_text[7] != "-":
        return None

    try:
        entered_date = date.fromisoformat(date_text)
    except ValueError:
        return None

    return entered_date


def add_years(start_date, years):
    """Return a date a whole number of calendar years after start_date."""
    try:
        return start_date.replace(year=start_date.year + years)
    except ValueError:
        # February 29 becomes February 28 when the destination year is not leap.
        return start_date.replace(year=start_date.year + years, month=2, day=28)


def approve_borrowing(data, borrowing_id, due_date):
    """Approve a request using today's date as the borrowed date."""
    record = find_by_id(data["borrowings"], borrowing_id)
    if record == None or record["status"] != "Pending":
        return False, "Pending borrowing record was not found."
    borrowed = date.today()
    due = parse_date(due_date)
    if due is None:
        return False, "Use YYYY-MM-DD - (Example: 2026-06-26)"
    if due < borrowed:
        return False, "Due date cannot be earlier than the borrowed date."
    if due > add_years(borrowed, 2):
        return False, "Due date cannot be more than two years after the borrowed date."

    record["status"] = "Borrowed"
    record["borrowed_date"] = borrowed.isoformat()
    record["due_date"] = due_date
    return True, "Borrowing request approved."


def receive_return(data, borrowing_id, condition, notes):
    """Record a return using today's date as the returned date."""
    record = find_by_id(data["borrowings"], borrowing_id)
    if record == None or record["status"] != "Borrowed":
        return False, "Borrowed record was not found."
    if condition != "Good" and condition != "Damaged" and condition != "Needs Repair":
        return False, "Choose Good, Damaged, or Needs Repair."
    returned = date.today()
    record["status"] = "Returned"
    record["returned_date"] = returned.isoformat()
    record["return_condition"] = condition
    record["notes"] = normalize_text(notes)

    item = find_by_id(data["equipment"], record["equipment_id"])
    if item is not None:
        # Return the reserved unit to the available stock.  Its condition is
        # retained so damaged equipment remains unavailable for staff action.
        item["quantity"] += 1
        item["condition"] = condition
    return True, "Return recorded successfully."


def mark_missing(data, borrowing_id, notes):
    """Mark an actively borrowed item as missing and save the explanation."""
    record = find_by_id(data["borrowings"], borrowing_id)
    if record == None or record["status"] != "Borrowed":
        return False, "Borrowed record was not found."

    record["status"] = "Missing"
    record["notes"] = normalize_text(notes)
    return True, "Item marked as missing."


def get_records_by_status(data, status):
    """Return every borrowing record with the requested status."""
    matching_records = []
    for record in data["borrowings"]:
        if record["status"] == status:
            matching_records.append(record)
    return matching_records


def get_overdue_records(data):
    """Return borrowed records whose due date is earlier than today."""
    overdue_records = []
    today = date.today()

    for record in data["borrowings"]:
        if record["status"] != "Borrowed":
            continue

        try:
            due_date = date.fromisoformat(record["due_date"])
        except ValueError:
            continue

        if due_date < today:
            overdue_records.append(record)

    return overdue_records


def get_student_records(data, student_id):
    """Return all borrowing records that belong to one student."""
    matching_records = []
    for record in data["borrowings"]:
        if record["student_id"] == student_id:
            matching_records.append(record)
    return matching_records



# Student accounts start empty.  They are created through the registration menu
# and are kept only while this program is running.

"""HardCoded Storage Data"""
STUDENTS = []

STAFF = [
    {
            "id": 1,
            "role": "staff",
            "name": "Equipment Staff",
            "school_id": "STAFF-001",
            "username": "admin",
            "password": "admin12345678",
     }
]


EQUIPMENT = [
    {
        "id": 1,
        "name": "Projector",
        "category": "Electronics",
        "asset_number": "EQ-001",
        "quantity": 2,
        "condition": "Good",
    },
    {
        "id": 2,
        "name": "Laptop",
        "category": "Electronics",
        "asset_number": "EQ-002",
        "quantity": 2,
        "condition": "Good",
    },
]

BORROWINGS = []

NEXT_IDS = {"student": 1, "staff": 2, "equipment": 3, "borrowing": 1}


def get_data():
    """Build the in-memory storage dictionary used by all program features."""
    data = {
        "students": STUDENTS,
        "staff": STAFF,
        "equipment": EQUIPMENT,
        "borrowings": BORROWINGS,
        "next_ids": NEXT_IDS,
    }
    return data



def divider():
    """Print a separator line to make console output easier to read."""
    print("-" * 60)


MAX_FAILED_ATTEMPTS = 3


def record_failed_attempt(failed_attempts, destination):
    """Count an invalid entry and report whether the current input flow must end."""
    failed_attempts += 1
    if failed_attempts == MAX_FAILED_ATTEMPTS:
        print("Too many invalid attempts. Returning to " + destination + ".")
        return failed_attempts, True

    remaining_attempts = MAX_FAILED_ATTEMPTS - failed_attempts
    print(str(remaining_attempts) + " attempt(s) remaining.")
    return failed_attempts, False


def number_input(message):
    """Return a whole number, or None when the user enters an invalid value."""
    value = input(message)
    if value.isdigit():
        return int(value)
    print("Please enter numbers only. Try again.")
    return None


def fit_cell(value, width):
    """Pad one value so it aligns with the other values in its column."""
    return str(value).ljust(width)


def print_table(headers, rows):
    """Print an aligned table that shows each value in full."""
    widths = []
    for index, header in enumerate(headers):
        longest_value = len(str(header))
        for row in rows:
            longest_value = max(longest_value, len(str(row[index])))
        widths.append(longest_value)

    border = "+-" + "-+-".join("-" * width for width in widths) + "-+"

    def print_row(row):
        cells = []
        for index, value in enumerate(row):
            cells.append(fit_cell(value, widths[index]))
        print("| " + " | ".join(cells) + " |")

    print(border)
    print_row(headers)
    print(border)
    for row in rows:
        print_row(row)
    print(border)


def print_equipment(data, available_only, show_asset_number=False):
    """Display equipment details, with asset numbers available only to staff."""
    headers = ["ID", "Name", "Category", "Quantity", "Condition"]
    if show_asset_number:
        headers.insert(1, "Asset Number")

    rows = []
    for item in data["equipment"]:
        status = equipment_status(data, item)
        if available_only == False or status == "Available":
            row = [item["id"], item["name"], item["category"], item["quantity"], item["condition"]]
            if show_asset_number:
                row.insert(1, item["asset_number"])
            rows.append(row)

    divider()
    print("EQUIPMENT")
    if rows == []:
        print("No equipment found.")
        return False

    print_table(headers, rows)
    return True


def print_records(data, records):
    """Display borrowing records in an aligned table."""
    if records == []:
        print("No borrowing records found.")
        return

    rows = []
    for record in records:
        item = find_by_id(data["equipment"], record["equipment_id"])
        student = find_by_id(data["students"], record["student_id"])
        rows.append([
            record["id"],
            item["name"],
            student["name"],
            record["borrowed_date"],
            record["due_date"],
            record["returned_date"],
            record["return_condition"],
            record["notes"],
        ])

    divider()
    print("BORROWING RECORDS")
    print_table(
        ["Record ID", "Equipment", "Student", "Borrowed", "Due Date", "Returned", "Condition", "Notes"],
        rows,
    )


def print_students(data):
    """Display registered students and return whether at least one exists."""
    divider()
    print("Students:")
    rows = []
    for user in data["students"]:
        if user["role"] == "student":
            rows.append([user["id"], user["name"], user["school_id"]])

    if rows == []:
        print("No student accounts found.")
        return False

    print_table(["ID", "Full Name", "School ID"], rows)
    return True


def choose_student(data):
    """Let staff select a student, returning after three invalid entries."""
    if print_students(data) == False:
        return None

    failed_attempts = 0
    while True:
        student_id = number_input("Enter student account ID: ")
        if student_id == None:
            failed_attempts, should_return = record_failed_attempt(
                failed_attempts, "the Equipment Records menu"
            )
            if should_return:
                return None
            print_students(data)
            continue
        student = find_by_id(data["students"], student_id)
        if student != None and student["role"] == "student":
            return student
        print("Student was not found. Try again.")
        failed_attempts, should_return = record_failed_attempt(
            failed_attempts, "the Equipment Records menu"
        )
        if should_return:
            return None
        print_students(data)


def student_menu(data, student):
    while True:
        divider()
        print("STUDENT MENU - " + student["name"])
        print("1. View available equipment")
        print("2. Request equipment")
        print("3. View my borrowing records")
        print("4. Log out")

        choice = input("Choose an option: ")
        if choice == "1":
            print_equipment(data, True)
            
        elif choice == "2":
            if print_equipment(data, True) == False:
                continue
            failed_attempts = 0
            while True:
                equipment_id = number_input("Enter equipment ID: ")
                if equipment_id == None:
                    failed_attempts, should_return = record_failed_attempt(
                        failed_attempts, "the Student Menu"
                    )
                    if should_return:
                        break
                    print_equipment(data, True)
                    continue
                success, message = request_borrowing(data, student, equipment_id)
                print(message)
                if success:
                    break
                failed_attempts, should_return = record_failed_attempt(
                    failed_attempts, "the Student Menu"
                )
                if should_return:
                    break
                print_equipment(data, True)
            
        elif choice == "3":
            records = get_student_records(data, student["id"])
            print_records(data, records)
            
        elif choice == "4":
            return
        else:
            print("Invalid option. Please choose 1 to 4.")


def staff_equipment_views(data):
    """Show staff-only record views after printing the equipment list."""
    while True:
        divider()
        print("EQUIPMENT RECORDS")
        print("1. View borrowed equipment")
        print("2. View missing items")
        print("3. View students")
        print("4. Student's records")
        print("5. View overdue equipment")
        print("6. View returned equipment")
        print("7. Back")
        choice = input("Choose an option: ")

        if choice == "1":
            print_records(data, get_records_by_status(data, "Borrowed"))
        elif choice == "2":
            print_records(data, get_records_by_status(data, "Missing"))
        elif choice == "3":
            print_students(data)
        elif choice == "4":
            student = choose_student(data)
            if student is not None:
                print_records(data, get_student_records(data, student["id"]))
        elif choice == "5":
            print_records(data, get_overdue_records(data))
        elif choice == "6":
            print_records(data, get_records_by_status(data, "Returned"))
        elif choice == "7":
            return
        else:
            print("Invalid option. Please choose a number from 1 to 7.")


def staff_menu(data, staff):
    while True:
        divider()
        print("STAFF MENU - " + staff["name"])
        print("1. View all equipment, student records.")
        print("2. Add equipment")
        print("3. Update equipment condition")
        print("4. Approve a Request")
        print("5. Receive a return")
        print("6. Mark item as missing")
        print("7. Log out")

        choice = input("Choose an option: ")
        
        
        if choice == "1":
            print_equipment(data, False, True)
            staff_equipment_views(data)
            
        elif choice == "2":
            failed_attempts = 0
            while True:
                name = input("Equipment name: ")
                asset_number = input("Asset number: ")
                quantity = input("Quantity: ")
                success, message = add_equipment(data, name, asset_number, quantity)
                print(message)
                if success:
                    break
                failed_attempts, should_return = record_failed_attempt(
                    failed_attempts, "the Staff Menu"
                )
                if should_return:
                    break
            
        elif choice == "3":
            print_equipment(data, False, True)
            failed_attempts = 0
            while True:
                equipment_id = number_input("Enter equipment ID to edit: ")
                if equipment_id == None:
                    failed_attempts, should_return = record_failed_attempt(
                        failed_attempts, "the Staff Menu"
                    )
                    if should_return:
                        break
                    print_equipment(data, False, True)
                    continue
                print("Condition:")
                print("1. Good")
                print("2. Damaged")
                print("3. Needs Repair")
                condition_choice = input("Choose condition: ")

                if condition_choice == "1":
                    condition = "Good"
                elif condition_choice == "2":
                    condition = "Damaged"
                elif condition_choice == "3":
                    condition = "Needs Repair"
                else:
                    condition = ""

                if condition == "":
                    print("Invalid condition choice.")
                    failed_attempts, should_return = record_failed_attempt(
                        failed_attempts, "the Staff Menu"
                    )
                    if should_return:
                        break
                else:
                    success, message = edit_equipment_condition(data, equipment_id, condition)
                    print(message)
                    if success:
                        break
                    failed_attempts, should_return = record_failed_attempt(
                        failed_attempts, "the Staff Menu"
                    )
                    if should_return:
                        break
                    print_equipment(data, False, True)

        elif choice == "4":
            records = get_records_by_status(data, "Pending")
            print_records(data, records)
            if records == []:
                continue

            record_id = number_input("Enter pending record ID: ")
            if record_id is not None:
              due_date = input("Due date (YYYY-MM-DD): ")
              success, message = approve_borrowing(data, record_id, due_date)
              print(message)
            
        elif choice == "5":
            records = get_records_by_status(data, "Borrowed")
            print_records(data, records)
            if records == []:
                continue
            failed_attempts = 0
            while True:
                record_id = number_input("Enter borrowed record ID: ")
                if record_id == None:
                    failed_attempts, should_return = record_failed_attempt(
                        failed_attempts, "the Staff Menu"
                    )
                    if should_return:
                        break
                    print_records(data, records)
                    continue
                print("Return condition:")
                print("1. Good")
                print("2. Damaged")
                print("3. Needs Repair")
                condition_choice = input("Choose condition: ")
                if condition_choice == "1":
                    condition = "Good"
                elif condition_choice == "2":
                    condition = "Damaged"
                elif condition_choice == "3":
                    condition = "Needs Repair"
                else:
                    condition = ""
                if condition == "":
                    print("Invalid condition choice. Please choose 1, 2, or 3.")
                    failed_attempts, should_return = record_failed_attempt(
                        failed_attempts, "the Staff Menu"
                    )
                    if should_return:
                        break
                    records = get_records_by_status(data, "Borrowed")
                    print_records(data, records)
                    continue
                notes = input("Notes: ")
                success, message = receive_return(data, record_id, condition, notes)
                print(message)
                if success:
                    break
                failed_attempts, should_return = record_failed_attempt(
                    failed_attempts, "the Staff Menu"
                )
                if should_return:
                    break
                records = get_records_by_status(data, "Borrowed")
                print_records(data, records)
            
        elif choice == "6":
            records = get_records_by_status(data, "Borrowed")
            print_records(data, records)
            if records == []:
                continue
            failed_attempts = 0
            while True:
                record_id = number_input("Enter borrowed record ID: ")
                if record_id == None:
                    failed_attempts, should_return = record_failed_attempt(
                        failed_attempts, "the Staff Menu"
                    )
                    if should_return:
                        break
                    print_records(data, records)
                    continue
                notes = input("Reason or notes: ")
                success, message = mark_missing(data, record_id, notes)
                print(message)
                if success:
                    break
                failed_attempts, should_return = record_failed_attempt(
                    failed_attempts, "the Staff Menu"
                )
                if should_return:
                    break
                records = get_records_by_status(data, "Borrowed")
                print_records(data, records)
            
        elif choice == "7":
            return
        else:
            print("Invalid option. Please choose a number from 1 to 7.")


def main():
    data = get_data()
    while True:
        divider()
        print("GSD EQUIPMENT")
        print("Borrowing and Return Tracking System")
        print("1. Register student account")
        print("2. Sign in")
        print("3. Exit")

        choice = input("Choose an option: ")
        if choice == "1":
            failed_attempts = 0
            while True:
                school_id = input("School ID: ")
                first_name = input("First name: ")
                middle_name = input("Full middle name: ")
                last_name = input("Last name: ")
                username = input("Username: ")
                password = input("Password: ")
                success, message = register_student(
                    data, first_name, middle_name, last_name, school_id, username, password
                )
                print(message)
                if success:
                    break
                failed_attempts, should_return = record_failed_attempt(
                    failed_attempts, "the main menu"
                )
                if should_return:
                    break
            
        elif choice == "2":
            failed_attempts = 0
            while True:
                username = input("Username: ")
                password = input("Password: ")
                user = find_user(data, username, password)
                if user == None:
                    failed_attempts += 1
                    if failed_attempts == 3:
                        print("Too many incorrect attempts. Returning to the main menu.")
                        break
                    remaining_attempts = 3 - failed_attempts
                    print("Incorrect username or password. " + str(remaining_attempts) + " attempt(s) remaining.")
                elif user["role"] == "staff":
                    staff_menu(data, user)
                    break
                else:
                    student_menu(data, user)
                    break
        elif choice == "3":
            print("Thank you for using GSD Equipment")
            return
        else:
            print("Invalid option. Please choose 1, 2, or 3.")


if __name__ == "__main__":
    main()
