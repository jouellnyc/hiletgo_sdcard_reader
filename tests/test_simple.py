import os
import sdcard_helper
sdcard_helper.mount()
count = 0  # <--- Initialize ONCE here
for x in range(0, 100):
    try:
        print(os.listdir('/sd/'))
    except Exception as e:
        # This only runs if there WAS an error
        print(f"Error on attempt {x}: {e}")
    else:
        # This GUARANTEES it ran without exception
        count += 1
    finally:
        # This runs every time to show current progress
        print(f"Attempt {x} | Cumulative Successes: {count}")