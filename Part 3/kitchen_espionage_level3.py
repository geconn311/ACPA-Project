import random
import time

def run_rowhammer_level():
    print("=== LEVEL 3: ROWHAMMER ===")
    print("You are a sous chef with access to only certain rows of a freezer shelf.")
    print("You can access only the even rows, i.e. 2, 4, 6, 8, ...")
    print("Your goal is to gain access to the locked pantry.")
    print("The pantry access list is sitting on one of the odd shelves.")
    print("If you figure out a way to knock the list off the shelf, the Chef might just let you into the pantry!")
    print("However, the Prep Cook comes in and puts items back on the shelf, so be quick!")
    print("")
    print("Objective: Find which row is near the one containing the hidden access list off the shelf.")
    print("           Knock it off through repeated accesses, then check with the Chef.")
    print("Constraint: You only have access to even-numbered rows (2, 4, 6 ... 18).")
    print("Warning: The Prep Cook resets the inventory every 35 actions!\n")

    # Base pantry items for shelves (1 through 20)
    # Automatically generate diverse pantry lists for the expanded rows
    pantry_pool = ["Box of pasta", "Bottle of olive oil", "Canned tomatoes", "Garlic cloves", 
                   "Bag of rice", "Black pepper shaker", "A jar of honey", "Bag of flour", 
                   "Box of salt", "Salt shaker", "Soy sauce bottle", "Vinegar bottle", 
                   "Dried oregano", "Butter block", "Milk carton", "Cheddar wedge", "Bag of sugar"]
    
    shelves = {}
    for i in range(1, 21):
        shelves[i] = random.sample(pantry_pool, k=random.randint(2, 4))

    # Pick a random target row from the odd rows (1, 3, 5 ... 19)
    valid_targets = [i for i in range(1, 20, 2)]
    target_row = random.choice(valid_targets)
    
    # Hide the Security Access List in the randomly chosen target row
    shelves[target_row].append("The Security Access List")

    # Accessible rows are even numbers from 2 to 18
    accessible_rows = [i for i in range(2, 20, 2)]
    
    actions_remaining = 35  
    access_list_fallen = False

    while actions_remaining > 0:
        print(f"--- Actions Remaining Before Inventory Reset: {actions_remaining} ---")
        print("Choices:")
        print("  [Even Rows 2-18] - Hammer a specific row (e.g., type 2, 4, 6...)")
        print("  [check]          - Ask the Chef to verify freezer access")
        print("  [quit]           - Exit game")
        
        choice = input("\nWhat do you want to do? ").strip().lower()

        if choice == "quit":
            print("You abandoned the kitchen.")
            return

        if choice == "check":
            print("\nYou walk up to the Head Chef and request entry...")
            time.sleep(1)
            if access_list_fallen:
                print("The Chef opens the ledger, looks around, and gasps.")
                print("'Wait... the access list is missing from the shelf! It must have fallen off.'")
                print("The Chef shrugs and unlocks the door. You win!")
                return
            else:
                print("The Chef checks the shelf. 'The access list is right here where it belongs. Get back to work!'")
                print("The check cost you precious time.")
                actions_remaining -= 3  # Asking the chef takes extra time penalty
            continue

        # Validate row input
        try:
            row_chosen = int(choice)
        except ValueError:
            print("Invalid input. Choose a valid row (2, 4, 6... 18) or type 'check'.\n")
            continue

        if row_chosen not in accessible_rows:
            print(f"Access Denied! You don't have permission to reach Row {row_chosen}.\n")
            continue

        # --- Rowhammer Action Logic ---
        print(f"\nYou aggressively pull and restock ingredients from Row {row_chosen}...")
        actions_remaining -= 1

        # Check physical adjacency to the randomly chosen target row
        if abs(row_chosen - target_row) == 1:
            print(f"-> Your hammering sends severe vibrations through the metal rack to a neighboring shelf...")
            
            target_items = shelves[target_row]
            if target_items:
                fallen_this_turn = []
                # Check each item on the target shelf independently (10% drop chance)
                for item in target_items[:]:
                    if random.random() < 0.10:
                        target_items.remove(item)
                        fallen_this_turn.append(item)
                
                if fallen_this_turn:
                    for item in fallen_this_turn:
                        if "Access List" in item:
                            print(f"-> You hear papers rustling. Something fluttered down to the floor!")
                            access_list_fallen = True
                        else:
                            print(f"-> *CLATTER/THUD* {item} slipped off the shelf and hit the floor!")
                else:
                    print("-> You hear metal groaning, but nothing manages to shake loose this time.")
            else:
                print("-> The target shelf is completely empty now!")
        else:
            print(f"-> A dull thud echoes from Row {row_chosen}, but it's too far away to disturb any sensitive shelves.")

        print()  # Empty line for readability

    # Failure condition if actions run out
    print("--- INVENTORY RESET ---")
    print("The Prep Cook walks in, sees the disturbed shelves, and puts everything back in order.")
    print("Your progress has been wiped out! Game Over.")

if __name__ == "__main__":
    run_rowhammer_level()