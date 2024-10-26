import ascii_magic
from ascii_magic import Front, Back
import time
import random
import os


def generate_ascii_art(image_path, color):
    art = ascii_magic.from_image_file(image_path, columns=60, char="#")
    return art.to_ascii(columns=60, color=color)


def display_emergency_call(priority, description, image_path):
    if priority == "High":
        color = Front.RED
    elif priority == "Medium":
        color = Front.YELLOW
    else:
        color = Front.GREEN

    art = generate_ascii_art(image_path, color)
    print(art)
    print(f"Priority: {priority}")
    print(f"Description: {description}")
    print("-" * 60)


def main():
    logo_path = os.path.join("assets", "urgent.jpg")
    print(generate_ascii_art(logo_path, Front.BLUE))
    print("Call Prioritization System")
    print("=" * 60)

    calls = [
        ("High", "Heart attack at 123 Main St", os.path.join("assets", "urgent.jpg")),
        ("Medium", "Car accident on Highway 1", os.path.join("assets", "medium.jpg")),
        ("Low", "Noise complaint at 456 Elm St", os.path.join("assets", "low.png")),
    ]

    while True:
        for priority, description, image_path in calls:
            display_emergency_call(priority, description, image_path)
            time.sleep(2)  # Wait for 2 seconds before displaying the next call

        print("\nPrioritizing calls...\n")
        time.sleep(1)
        random.shuffle(calls)  # Simulate prioritization by shuffling the list


if __name__ == "__main__":
    main()
