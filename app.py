from flask import Flask, render_template, request, redirect, url_for, session
from flask import send_file, Response
from flask import flash
from decouple import config
import csv
import io
import mysql.connector

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = 'your_secret_key'


# ############### Function to connect to the SQLite database  ###############
def connect_db():
    return mysql.connector.connect(
        host=config('DB_HOST'),
        user=config('DB_USER'),
        password=config('DB_PASSWORD'),
        database=config('DB_DATABASE')
    )

# ############### Route for the login page #######################################
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

# ####################################### Route for the dashboard (requires login) #######################################
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM PersonalInformation')
    total_count = cursor.fetchone()[0]

    conn.close()

    return render_template('dashboard.html',total_count=total_count, username=session['username'])

# Route to add a new student record
@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        conn = connect_db()
        cursor = conn.cursor()

        # Retrieve form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        middle_name = request.form['middle_name']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender']
        phone_number = request.form['phone_number']
        address = request.form['address']
        emergency_contact = request.form['emergency_contact']

        # Insert data into AcademicInformation table
        department = request.form['department']
        Mathematics = request.form['Mathematics']
        English = request.form['English']
        Chemistry = request.form['Chemistry']
        Physics = request.form['Physics']
        Biology = request.form['Biology']
        Computer = request.form['Computer']
        Commerce = request.form['Commerce']
        Acccounting = request.form['Acccounting']
        Literature = request.form['Literature']
        Government = request.form['Government']
        Economic = request.form['Economic']
        year_grade = int(request.form['year_grade'])

        conn.commit()

        # Insert new record into PersonalInformation table
        cursor.execute('''
            INSERT INTO PersonalInformation (first_name, last_name, middle_name, date_of_birth, gender, phone_number, address, emergency_contact)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (first_name, last_name, middle_name, date_of_birth, gender, phone_number, address, emergency_contact))

        # Get the last inserted ID for the foreign key reference
        student_id = cursor.lastrowid

        # Insert new record into AcademicInformation table
        cursor.execute('''
            INSERT INTO AcademicInformation 
            (student_id, department, Mathematics, English, Chemistry, Physics, Biology, Computer, Commerce, Acccounting, Literature, Government, Economic, year_grade)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (student_id, department, Mathematics, English, Chemistry, Physics, Biology, Computer, Commerce, Acccounting, Literature, Government, Economic, year_grade))

        conn.commit()
        conn.close()

        flash('Record successfully added to database', 'success')
        return redirect(url_for('view_students'))

    return render_template('add_student.html')

# ############### Route to view Transaction result ###############
@app.route("/result")
def result():
    return render_template("result.html")

# ############### Route to search for students ###############
@app.route('/search_students', methods=['GET'])
def search_students():
    search_query = request.args.get('search_query', '')

    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    # Use CONCAT function for string concatenation and LIKE '%...%'
    cursor.execute('''
    SELECT * FROM PersonalInformation
    WHERE id LIKE %(search_query)s
       OR first_name LIKE %(search_query)s
       OR last_name LIKE %(search_query)s
       OR middle_name LIKE %(search_query)s
''', {'search_query': '%' + search_query + '%'})

    searched_students = cursor.fetchall()

    conn.close()

    no_results_message = ""

    if not searched_students:
        no_results_message = "No records found for the search query."

    return render_template('search_results.html', searched_students=searched_students, search_query=search_query, no_results_message=no_results_message)

# ############### Route to download records as CSV ###############
@app.route('/download_records')
def download_records():
    conn = connect_db()
    cursor = conn.cursor()

    # Use aliases for the table names in the query
    cursor.execute('SELECT * FROM PersonalInformation AS p INNER JOIN AcademicInformation AS a ON p.id = a.student_id')
    data = cursor.fetchall()

    conn.close()

    # Prepare data for CSV file
    output = io.StringIO()
    csv_writer = csv.writer(output)

    # Write headers
    csv_writer.writerow([i[0] for i in cursor.description])

    # Write data
    csv_writer.writerows(data)

    # Create a response object to send the CSV file
    output.seek(0)

    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=student_data.csv'}
    )


    # return response
# Route for logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Route to view all student records
@app.route('/view_students')
def view_students():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM PersonalInformation')
    students = cursor.fetchall()

    conn.close()
    return render_template('view_students.html', students=students)



# Route to view academic student records

@app.route('/academic_Information', methods=['GET'])
def academic_Information():
    conn = connect_db()
    cursor = conn.cursor()

    # Fetch data from the database with a condition
    year_grade_threshold = 10  # Change this value as needed
    cursor.execute('SELECT * FROM AcademicInformation WHERE year_grade >= %s', (year_grade_threshold,))
    records = cursor.fetchall()

    conn.close()

    return render_template('academic_Information.html', records=records)


# Route to edit a student record
@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    if request.method == 'POST':
        conn = connect_db()
        cursor = conn.cursor()

        # Retrieve form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        middle_name = request.form['middle_name']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender']
        phone_number = request.form['phone_number']
        address = request.form['address']
        emergency_contact = request.form['emergency_contact']

        # Update data in PersonalInformation table
        cursor.execute('''
            UPDATE PersonalInformation
            SET first_name = %s, last_name = %s, middle_name = %s,
                date_of_birth = %s, gender = %s, phone_number = %s,
                address = %s, emergency_contact = %s
            WHERE id = %s
        ''', (first_name, last_name, middle_name, date_of_birth, gender, phone_number, address, emergency_contact, student_id))

        conn.commit()
        conn.close()

        # Send success message to view_student template
        flash('Record successfully updated in the database', 'success')
        return redirect(url_for('view_students'))

    else:
        # Fetch the current data for the selected student
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('SELECT * FROM PersonalInformation WHERE id = %s', (student_id,))
        student = cursor.fetchone()

        conn.close()

        if student:
            return render_template('edit_student.html', student=student)
        else:
            flash('Student not found', 'error')
            return redirect(url_for('view_students'))





# ##################ACADEMIC INFORMATION #######################

@app.route('/edit_acadInfo/<int:student_id>', methods=['GET', 'POST'])
def edit_acadInfo(student_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # Retrieve updated form data
        # ... (rest of your code)
        department = request.form['department']
        mathematics = request.form['Mathematics']
        english = request.form['English']
        chemistry = request.form['Chemistry']
        physics = request.form['Physics']
        biology = request.form['Biology']
        computer = request.form['Computer']
        commerce = request.form['Commerce']
        acccounting = request.form['Acccounting']  # Fix the column name here
        literature = request.form['Literature']
        government = request.form['Government']
        economic = request.form['Economic']
        year_grade = int(request.form['year_grade'])


        # Update AcademicInformation table
        cursor.execute('''
            UPDATE AcademicInformation
            SET department=%s, Mathematics=%s, English=%s, Chemistry=%s,
                Physics=%s, Biology=%s, Computer=%s, Commerce=%s, Acccounting=%s,
                Literature=%s, Government=%s, Economic=%s, year_grade=%s
            WHERE student_id=%s
        ''', (department, mathematics, english, chemistry, physics, biology, computer,
              commerce, acccounting, literature, government, economic, year_grade, student_id))

        conn.commit()
        conn.close()

        flash('Record successfully updated in the database', 'success')
        return redirect(url_for('academic_Information'))
    else:
        # Fetch existing data for the specified student_id
        cursor.execute('SELECT * FROM AcademicInformation WHERE student_id=%s', (student_id,))
        academic_info = cursor.fetchone()

        conn.close()

        # Render the edit form template with the existing data
        return render_template('edit_acadInfo.html', academic_info=academic_info)






# DELETE BUTTON 
@app.route('/delete_student/<int:student_id>', methods=['GET'])
def delete_student(student_id):
    conn = connect_db()
    cursor = conn.cursor()

    # Delete related records from AcademicInformation table first
    cursor.execute('DELETE FROM AcademicInformation WHERE student_id = %s', (student_id,))

    # Now, delete the student from the PersonalInformation table
    cursor.execute('DELETE FROM PersonalInformation WHERE id = %s', (student_id,))

    conn.commit()
    conn.close()

    # Send the transaction message to result.html
    flash('Record Successfully Deleted in database', 'success')  # Flash success message
    return redirect(url_for('view_students'))  # Redirect to the same view_students page

    # return redirect('/')  # Redirect back to the view_students page or any appropriate page


# Render the initial HTML page with the search bar
@app.route('/view_results')
def view_results():
    return render_template('view_results.html')


def calculate_percentage(scores):
    total_score = sum(scores)  # Calculate total score from subject scores
    percentage = (total_score / 700) * 100
    return round(percentage, 2)








# Function to fetch selected columns and calculate percentage score for each student
def fetch_selected_columns_with_percentage():
    conn = connect_db()
    cursor = conn.cursor()

    # Columns you want to fetch
    selected_columns = [
        'student_id', 'department', 'Mathematics', 'English', 'Chemistry', 
        'Physics', 'Biology', 'Computer', 'Commerce', 
        'Acccounting', 'Literature', 'Government', 'Economic'
    ]

    # Constructing the SQL SELECT query
    columns_str = ', '.join(selected_columns)
    select_query = f"SELECT {columns_str} FROM AcademicInformation"

    # Executing the query
    cursor.execute(select_query)
    data = cursor.fetchall()

# Calculate percentage score for each student
    data_with_percentage = []
    for row in data:
        student_id = row[0]
        department = row[1]
        subjects_data = row[2:] 

        numeric_data = []
        for val in subjects_data:
            if isinstance(val, str) and val.strip():
                try:
                    numeric_data.append(float(val))
                except ValueError:
                    numeric_data.append(0.0)
            elif isinstance(val, int) or isinstance(val, float):
                numeric_data.append(float(val))
            else:
                numeric_data.append(0.0)

        total_score = sum(numeric_data)
        max_possible_score = 7 * 100  # Considering 10 subjects with a maximum score of 100 each

        percentage_score = 0.0  # Default to 0.0 if no valid subjects found
        if max_possible_score > 0:
            percentage_score = (total_score / max_possible_score) * 100

    # Round the percentage_score to one decimal place
        percentage_score = round(percentage_score, 1)

       # Create a new tuple including existing data and the percentage score
        row_with_percentage = (student_id, department, *subjects_data, percentage_score)
        data_with_percentage.append(row_with_percentage)
    conn.close()
    return data_with_percentage




# Route to display the selected columns
@app.route('/view-selected-columns')
def view_selected_columns():
    academic_data = fetch_selected_columns_with_percentage()
    return render_template('selected_columns.html', academic_data=academic_data)





if __name__ == '__main__':
    app.run()
