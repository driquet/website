import matplotlib.pyplot as plt
import numpy as np

x_values = [f"{i}" for i in range (1, 26)]

counts = {
    'Part One': [
        24, 3.25, 7.75, 9.52, 3,
        3.30, 8.30, 5, 24, 24,
        6.20, 4.30, 4.30, 3.75, 4,
        3.5, 17.90, 3.5, 1.25, 24,
        24, 24, 9.5, 5.25, 5.35,
    ],
    'Part Two': [
        24, 3.25, 8, 16.25, 12.95,
        11.95, 9, 5.20, 24, 24,
        6.35, 12.25, 4.5, 4.29, 7.19,
        3.55, 24, 4, 3.28, 24,
        24, 24, 10.19, 15.72, 5.46,
    ],
}

# Set the xkcd style
plt.xkcd()

# Create a line plot for each series
for series, series_counts in counts.items():
    plt.plot(x_values, series_counts, marker='o', label=series)

# Adding labels and title
plt.xlabel('Day')
plt.ylabel('Elapsed time (h) since challenge release')
plt.title('Challenge Completion Times for Part One and Part Two')
plt.xticks(x_values)  # Set x-ticks
plt.ylim(0, 25)  # Set y-axis limits to give some space above the lines
plt.legend(title='Parts')

# Show the plot
plt.show()
