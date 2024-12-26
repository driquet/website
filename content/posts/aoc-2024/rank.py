import matplotlib.pyplot as plt
import numpy as np

x_values = [f"{i}" for i in range (1, 26)]

counts = {
    'Part One': [
        112530, 29273, 55924, 48233, 20948,
        20803, 30650, 19163, 49334, 44014,
        27172, 15208, 14566, 11676, 10698,
        7906, 23865, 10011, 5861, 20533,
        14117, 19778, 14307, 10235, 10242,
    ], 
    'Part Two': [
        105914, 19948, 46802, 61880, 44084,
        28955, 29008, 17308, 39122, 43027,
        17829, 16886, 10188, 9297, 8688,
        5069, 18382, 9672, 7604, 17533,
        11406, 16951, 11860, 7759, 6668,
    ],
}

# Set the xkcd style
plt.xkcd()

# Create a line plot for each series
for series, series_counts in counts.items():
    plt.plot(x_values, series_counts, marker='o', label=series)

# Adding labels and title
plt.xlabel('Day')
plt.ylabel('Rank')
plt.title('Ranking for Part One and Part Two')
plt.xticks(x_values)  # Set x-ticks
# plt.ylim(0, 25)  # Set y-axis limits to give some space above the lines
plt.legend(title='Parts')

# Show the plot
plt.show()
