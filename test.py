import sqlite3


def export_to_markdown(db_path, query, output_file):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]

    with open(output_file, 'w') as f:
        # Write header
        f.write("| " + " | ".join(column_names) + " |\n")
        # Write separator
        f.write("|" + "---|" * len(column_names) + "\n")
        # Write data rows
        for row in rows:
            f.write("| " + " | ".join(map(str, row)) + " |\n")

    conn.close()


# Example usage:
export_to_markdown('db.sqlite3', 'SELECT * FROM anime_anime;', 'users.md')
