import matplotlib.pyplot as plt
import io
from utils.i18n import get_text

def create_expense_pie_chart(data, lang='uz'):
    """
    Creates a pie chart from expense data.
    data: list of tuples (category_name, amount)
    Returns: BytesIO object containing the image data
    """
    if not data:
        return None

    categories = [row[0] for row in data]
    amounts = [row[1] for row in data]

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Premium look: use a nice color palette
    colors = plt.cm.Paired(range(len(categories)))
    
    wedges, texts, autotexts = ax.pie(
        amounts, 
        labels=categories, 
        autopct='%1.1f%%', 
        startangle=140, 
        colors=colors,
        pctdistance=0.85,
        explode=[0.05] * len(categories) # Add slight separation
    )

    # Style the text
    plt.setp(autotexts, size=10, weight="bold", color="white")
    plt.setp(texts, size=12)

    # Draw a circle at the center to make it a donut chart (optional, looks more modern)
    centre_circle = plt.Circle((0,0), 0.70, fc='white')
    fig.gca().add_artist(centre_circle)

    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title(get_text('chart_title', lang), fontsize=14, pad=20)

    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    
    return buf
